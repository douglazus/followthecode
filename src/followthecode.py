import os
import csv
import statistics
import collections
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox
from pydriller import Repository

def analyze_repo(repo_path):
    """
    Analyzes a Git repository over the last 90 days and outputs various metrics to CSV files.
    """

    # Time range
    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=90)

    # Data structures
    commits_por_autor = collections.Counter()
    modificacoes_por_arquivo = collections.Counter()
    autores_por_arquivo = {}
    linhas_adicionadas_por_autor = collections.Counter()
    linhas_removidas_por_autor = collections.Counter()
    churn_por_autor = collections.Counter()
    commits_por_dia_semana = collections.Counter()
    datas_commits_por_autor = collections.defaultdict(list)

    # Mining the repository
    for commit in Repository(
        repo_path,
        since=data_inicio,
        to=data_fim
    ).traverse_commits():
        autor = commit.author.name
        data_commit = commit.author_date

        # Commits per author
        commits_por_autor[autor] += 1

        # Weekday of the commit (Monday=0 ... Sunday=6)
        dia_semana = data_commit.weekday()
        commits_por_dia_semana[dia_semana] += 1

        # Store commit dates for average commit time calculation
        datas_commits_por_autor[autor].append(data_commit)

        # File modifications
        for modificacao in commit.modifications:
            arquivo = modificacao.new_path
            if arquivo:
                modificacoes_por_arquivo[arquivo] += 1

                if arquivo not in autores_por_arquivo:
                    autores_por_arquivo[arquivo] = set()
                autores_por_arquivo[arquivo].add(autor)

                # Lines added/removed
                linhas_adicionadas_por_autor[autor] += modificacao.added
                linhas_removidas_por_autor[autor] += modificacao.removed
                churn_por_autor[autor] += (modificacao.added + modificacao.removed)

    # Create an output folder (if desired) to store CSVs
    output_folder = os.path.join(repo_path, "analysis_results")
    os.makedirs(output_folder, exist_ok=True)

    # 1) Commits per author
    with open(os.path.join(output_folder, "authors_commits.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Author", "Commits"])
        for autor, qtd_commits in commits_por_autor.most_common():
            writer.writerow([autor, qtd_commits])

    # 2) Most modified files (top 10)
    with open(os.path.join(output_folder, "most_modified_files.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Modifications"])
        for arquivo, qtd_mod in modificacoes_por_arquivo.most_common(10):
            writer.writerow([arquivo, qtd_mod])

    # 3) Files with the most authors
    arquivos_por_autores_count = [(arq, len(autores)) for arq, autores in autores_por_arquivo.items()]
    arquivos_por_autores_count.sort(key=lambda x: x[1], reverse=True)

    with open(os.path.join(output_folder, "files_authors.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Filename", "Number_of_Authors"])
        for arquivo, num_autores in arquivos_por_autores_count[:10]:
            writer.writerow([arquivo, num_autores])

    # 4) Author with most added lines
    with open(os.path.join(output_folder, "added_lines_by_author.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Author", "Added_Lines"])
        for autor, added_lines in linhas_adicionadas_por_autor.most_common():
            writer.writerow([autor, added_lines])

    # 5) Author with most removed lines
    with open(os.path.join(output_folder, "removed_lines_by_author.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Author", "Removed_Lines"])
        for autor, removed_lines in linhas_removidas_por_autor.most_common():
            writer.writerow([autor, removed_lines])

    # 6) Code churn (added + removed) by author
    with open(os.path.join(output_folder, "code_churn_by_author.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Author", "Code_Churn"])
        for autor, churn in churn_por_autor.most_common():
            writer.writerow([autor, churn])

    # 7) Commits by weekday
    # 0=Monday, 1=Tuesday, ..., 6=Sunday
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    with open(os.path.join(output_folder, "commits_by_weekday.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Weekday", "Commits"])
        for dia, qtd in commits_por_dia_semana.most_common():
            writer.writerow([weekday_names[dia], qtd])

    # 8) Average time between commits by author (in hours)
    with open(os.path.join(output_folder, "average_commit_time_by_author.csv"), "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Author", "Average_Time_Between_Commits_(hours)"])
        for autor, datas in datas_commits_por_autor.items():
            if len(datas) > 1:
                datas.sort()
                intervals = []
                for i in range(1, len(datas)):
                    diff = datas[i] - datas[i-1]
                    intervals.append(diff.total_seconds() / 3600.0)
                avg_hours = statistics.mean(intervals)
                writer.writerow([autor, f"{avg_hours:.2f}"])
            else:
                writer.writerow([autor, "Only one commit - no average time"])

    messagebox.showinfo("Analysis Complete", f"Analysis files saved in:\n{output_folder}")


def select_repo():
    """
    Opens a Tkinter dialog to select a folder (Git repo),
    then calls analyze_repo on that folder.
    """
    folder_selected = filedialog.askdirectory(title="Select your Git repository folder")
    if folder_selected:
        analyze_repo(folder_selected)


def main():
    root = tk.Tk()
    root.title("Git Repository Analyzer")

    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    width, height = 400, 200

    # Center the window on the screen
    x = (screen_width // 2) - (width // 2)
    y = (screen_height // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    label = tk.Label(root, text="Select a Git repository folder to analyze\n(Last 90 days).", font=("Arial", 12))
    label.pack(pady=20)

    button = tk.Button(root, text="Select Repository", command=select_repo, font=("Arial", 10))
    button.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
