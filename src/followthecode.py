import os
import csv
import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
from git import Repo

def select_repository():
    """
    Abre uma janela para o usuário selecionar o diretório do repositório Git.
    Retorna o caminho selecionado (string) ou None caso nada seja selecionado.
    """
    root = tk.Tk()
    root.withdraw()
    repo_path = filedialog.askdirectory(title='Selecione o diretório do repositório Git')
    root.destroy()
    if repo_path:
        return repo_path
    else:
        return None

def get_active_branch(repo):
    """
    Retorna o branch principal ('master' ou 'main') ou outro branch caso não encontre.
    Essa função tenta primeiro 'master'; se não existir, tenta 'main'; 
    se não existir, retorna o branch ativo.
    """
    branches = [b.name for b in repo.branches]
    if 'master' in branches:
        return 'master'
    elif 'main' in branches:
        return 'main'
    else:
        # Se não tiver master ou main, retorna o branch atual
        return repo.active_branch.name

def get_commits_in_last_3_months(repo, branch):
    """
    Retorna os commits de 'branch' dos últimos 3 meses com base na data atual (hoje).
    """
    now = datetime.datetime.now()
    three_months_ago = now - datetime.timedelta(days=90)
    
    commits = list(repo.iter_commits(branch))
    
    # Filtra por data >= three_months_ago
    commits_filtered = []
    for commit in commits:
        commit_date = datetime.datetime.fromtimestamp(commit.committed_date)
        if commit_date >= three_months_ago:
            commits_filtered.append(commit)
    
    return commits_filtered

def get_commits_from_last_commit(repo, branch):
    """
    1) Identifica o último commit (mais recente).
    2) Retorna os commits dos últimos 3 meses a partir da data do último commit.
    Se não houver commits nesse intervalo, devolve lista vazia.
    """
    commits = list(repo.iter_commits(branch))
    if not commits:
        return []
    
    # O primeiro da lista costuma ser o mais recente (iter_commits já traz em ordem desc)
    last_commit = commits[0]
    last_commit_date = datetime.datetime.fromtimestamp(last_commit.committed_date)
    
    # 3 meses antes do último commit
    three_months_before_last = last_commit_date - datetime.timedelta(days=90)
    
    commits_filtered = []
    for commit in commits:
        commit_date = datetime.datetime.fromtimestamp(commit.committed_date)
        # Fica dentro do intervalo [three_months_before_last, last_commit_date]
        if three_months_before_last <= commit_date <= last_commit_date:
            commits_filtered.append(commit)
            
    return commits_filtered

def generate_metrics(repo, commits):
    """
    Gera diversas métricas a partir de uma lista de commits:
    
    - Commits por autor
    - Arquivos modificados (linhas adicionadas, removidas, total)
    - Arquivos com maior número de autores
    - Linhas adicionadas/removidas por autor
    - Code churn (added + removed) por autor
    - Commits por dia da semana
    - Average time between commits por autor (em horas)
    - Autores com mais commits
    - Arquivos mais modificados por autor
    
    Retorna um dicionário com várias estruturas de dados que depois serão 
    salvas em CSV por outra função.
    """

    # Para algumas métricas, precisamos de commits em ordem cronológica
    # (do mais antigo para o mais recente) para calcular intervalos.
    # Normalmente, list(repo.iter_commits()) vem do mais recente para o mais antigo.
    # Então vamos ordenar manualmente pelo committed_date (asc).
    commits_sorted = sorted(commits, key=lambda c: c.committed_date)

    # Dicionários que vão armazenar as métricas:
    commits_by_author = {}  # autor -> contagem de commits
    file_stats = {}         # filename -> {'insertions': x, 'deletions': y, 'authors': set(...) }
    lines_by_author = {}    # autor -> {'insertions': x, 'deletions': y}
    commits_by_day = {}     # nome_dia_semana -> contagem
    last_commit_time_by_author = {}     # autor -> data/hora do último commit (para calcular intervalos)
    time_diffs_by_author = {}           # autor -> [lista de diferenças em horas]
    
    # Para sabermos quanto cada (autor, arquivo) modificou
    # file_changes_by_author[filename][author] = total_linhas_modificadas
    file_changes_by_author = {}

    for commit in commits_sorted:
        commit_date = datetime.datetime.fromtimestamp(commit.committed_date)
        day_of_week = commit_date.strftime('%A')  # Monday, Tuesday, etc.
        author = str(commit.author)

        # --- Contagem de commits por autor ---
        commits_by_author[author] = commits_by_author.get(author, 0) + 1

        # --- Commits por dia da semana ---
        commits_by_day[day_of_week] = commits_by_day.get(day_of_week, 0) + 1

        # --- Calculo do tempo entre commits por autor ---
        if author not in time_diffs_by_author:
            time_diffs_by_author[author] = []
        if author in last_commit_time_by_author:
            diff_hours = (commit_date - last_commit_time_by_author[author]).total_seconds() / 3600.0
            time_diffs_by_author[author].append(diff_hours)
        last_commit_time_by_author[author] = commit_date

        # Pega as estatísticas (arquivos modificados, inserções, deleções, etc.)
        stats = commit.stats

        for file_name, file_stat in stats.files.items():
            insertions = file_stat['insertions']
            deletions = file_stat['deletions']
            total_changes = insertions + deletions

            # --- Atualiza stats do arquivo ---
            if file_name not in file_stats:
                file_stats[file_name] = {
                    'insertions': 0,
                    'deletions': 0,
                    'authors': set()
                }
            file_stats[file_name]['insertions'] += insertions
            file_stats[file_name]['deletions'] += deletions
            file_stats[file_name]['authors'].add(author)

            # --- Atualiza lines_by_author ---
            if author not in lines_by_author:
                lines_by_author[author] = {'insertions': 0, 'deletions': 0}
            lines_by_author[author]['insertions'] += insertions
            lines_by_author[author]['deletions'] += deletions

            # --- Atualiza file_changes_by_author ---
            if file_name not in file_changes_by_author:
                file_changes_by_author[file_name] = {}
            if author not in file_changes_by_author[file_name]:
                file_changes_by_author[file_name][author] = 0
            file_changes_by_author[file_name][author] += total_changes

    # Agora que coletamos todos os dados, podemos extrair algumas informações:

    # 1) Authors with most commits (é só ordenar commits_by_author por valor desc)
    authors_with_most_commits = sorted(commits_by_author.items(), key=lambda x: x[1], reverse=True)

    # 2) Most modified files (ordenar pela soma de (inserions + deletions))
    files_modified_list = []
    for f, stats in file_stats.items():
        total_changes = stats['insertions'] + stats['deletions']
        files_modified_list.append((f, stats['insertions'], stats['deletions'], total_changes))
    files_modified_list.sort(key=lambda x: x[3], reverse=True)  # ordena por total_changes desc

    # 3) Files com o maior número de autores
    files_by_authors_count = []
    for f, stats in file_stats.items():
        n_authors = len(stats['authors'])
        files_by_authors_count.append((f, n_authors))
    files_by_authors_count.sort(key=lambda x: x[1], reverse=True)

    # 4) Lines added/removed by author + code churn
    # code_churn = insertions + deletions
    lines_author_list = []
    for author, val in lines_by_author.items():
        insertions = val['insertions']
        deletions = val['deletions']
        churn = insertions + deletions
        lines_author_list.append((author, insertions, deletions, churn))
    lines_author_list.sort(key=lambda x: x[3], reverse=True)  # ordena desc por churn

    # 5) Commits by day of the week
    # Basta extrair o dicionário (commits_by_day) e ordenar, se quiser
    commits_by_day_list = sorted(commits_by_day.items(), key=lambda x: x[0])  # alphabético p.ex.

    # 6) Average time between commits (em horas) por autor
    average_time_by_author = []
    for author, diffs in time_diffs_by_author.items():
        if len(diffs) > 0:
            avg_time = sum(diffs) / len(diffs)
        else:
            # Se só tiver 1 commit do autor, não há "intervalo" para calcular
            avg_time = 0.0
        average_time_by_author.append((author, avg_time))
    average_time_by_author.sort(key=lambda x: x[1])  # ordena por menor tempo médio

    # 7) Files most changed by authors
    # É basicamente o dicionário file_changes_by_author, mas podemos transformar em lista
    # Formato: (file, author, lines_changed)
    files_most_changed_by_authors_list = []
    for f, authors_dict in file_changes_by_author.items():
        for auth, lines_changed in authors_dict.items():
            files_most_changed_by_authors_list.append((f, auth, lines_changed))
    # Ordenar por lines_changed desc
    files_most_changed_by_authors_list.sort(key=lambda x: x[2], reverse=True)

    # Retorna todas as métricas em um dicionário para podermos salvar em CSV depois
    return {
        'commits_by_author': commits_by_author,
        'authors_with_most_commits': authors_with_most_commits,
        'files_modified_list': files_modified_list,
        'files_by_authors_count': files_by_authors_count,
        'lines_author_list': lines_author_list,
        'commits_by_day_list': commits_by_day_list,
        'average_time_by_author': average_time_by_author,
        'files_most_changed_by_authors': files_most_changed_by_authors_list
    }

def save_metrics_to_csv(metrics):
    """
    Salva cada métrica em um CSV separado. O dicionário `metrics` vem de `generate_metrics()`.
    """

    # 1) Commits per author
    # O `commits_by_author` é {author: count}. Vamos salvar em commits_by_author.csv
    with open('commits_by_author.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['author', 'commits'])
        for author, count in metrics['commits_by_author'].items():
            writer.writerow([author, count])

    # 2) Authors with most commits -> authors_with_most_commits.csv
    # É uma lista de tuplas (author, count).
    with open('authors_with_most_commits.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['author', 'commits'])
        for author, count in metrics['authors_with_most_commits']:
            writer.writerow([author, count])

    # 3) Most modified files -> most_modified_files.csv
    # files_modified_list é [(file, insertions, deletions, total)]
    with open('most_modified_files.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['file', 'insertions', 'deletions', 'total_changes'])
        for file_name, ins, dels, total in metrics['files_modified_list']:
            writer.writerow([file_name, ins, dels, total])

    # 4) Files com o maior número de autores -> files_with_most_authors.csv
    # files_by_authors_count é [(file, n_authors)]
    with open('files_with_most_authors.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['file', 'num_authors'])
        for file_name, n_authors in metrics['files_by_authors_count']:
            writer.writerow([file_name, n_authors])

    # 5) Lines added/removed by author + code churn -> lines_by_author.csv
    # lines_author_list é [(author, insertions, deletions, churn)]
    with open('lines_by_author.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['author', 'insertions', 'deletions', 'code_churn'])
        for author, ins, dels, churn in metrics['lines_author_list']:
            writer.writerow([author, ins, dels, churn])

    # 6) Commits by day of the week -> commits_by_day.csv
    # commits_by_day_list é [(day_of_week, count)]
    with open('commits_by_day.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['day_of_week', 'commits'])
        for day, count in metrics['commits_by_day_list']:
            writer.writerow([day, count])

    # 7) Average time between commits by author -> average_time_between_commits.csv
    # average_time_by_author é [(author, avg_time_hours)]
    with open('average_time_between_commits.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['author', 'avg_time_between_commits_hours'])
        for author, avg_time in metrics['average_time_by_author']:
            writer.writerow([author, f"{avg_time:.2f}"])

    # 8) Files most changed by authors -> files_most_changed_by_authors.csv
    # files_most_changed_by_authors_list é [(file, author, lines_changed)]
    with open('files_most_changed_by_authors.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(['file', 'author', 'lines_changed'])
        for file_name, author, lines_changed in metrics['files_most_changed_by_authors']:
            writer.writerow([file_name, author, lines_changed])

def main():
    # 1. Selecionar o repositório via interface
    repo_path = select_repository()
    if not repo_path:
        messagebox.showinfo("Cancelado", "Nenhum repositório foi selecionado. Encerrando.")
        return

    # 2. Verifica se há .git na pasta
    if not os.path.isdir(os.path.join(repo_path, '.git')):
        messagebox.showerror("Erro", "O diretório selecionado não parece ser um repositório Git.")
        return

    # 3. Inicializa o repositório
    try:
        repo = Repo(repo_path)
    except Exception as e:
        messagebox.showerror("Erro", f"Não foi possível abrir o repositório. Detalhes: {str(e)}")
        return

    # 4. Identifica o branch principal ('master' ou 'main')
    branch_name = get_active_branch(repo)

    # --------------------------------------------------------------------------------
    # Lógica para pegar commits nos últimos 3 meses, senão do último commit, senão todos
    # --------------------------------------------------------------------------------
    commits_in_range = get_commits_in_last_3_months(repo, branch_name)
    if not commits_in_range:
        commits_in_range = get_commits_from_last_commit(repo, branch_name)
        if not commits_in_range:
            commits_in_range = list(repo.iter_commits(branch_name))

    if not commits_in_range:
        messagebox.showinfo("Informação", f"Não foram encontrados commits no branch '{branch_name}' no repositório.")
        return

    # 5. Gera métricas
    metrics = generate_metrics(repo, commits_in_range)

    # 6. Salva cada métrica em um CSV
    save_metrics_to_csv(metrics)

    # 7. Mensagem de sucesso
    messagebox.showinfo(
        "Sucesso", 
        f"Foram analisados {len(commits_in_range)} commits no branch '{branch_name}'.\n"
        "Relatórios gerados em CSV para cada métrica!"
    )

if __name__ == "__main__":
    main()
