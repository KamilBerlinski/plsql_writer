import os
import tempfile
import ollama
import subprocess
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

def summarize_sql(content):
    prompt = f"""
Jesteś asystentem SQL. Otrzymasz zapytanie SQL bez komentarzy.
Twoim zadaniem jest dodać na początku pliku komentarze w języku polskim, które krótko i jasno opisują, co robi zapytanie.
Używaj tylko komentarzy w formacie `-- komentarz`, nie używaj formatu /* ... */.
Zwróć pełen kod SQL z dodanymi komentarzami.

SQL:
{content}
"""
    response = ollama.chat(
        model="mistral",
        messages=[{"role": "user", "content": prompt}]
    )
    return response["message"]["content"]

def open_editor_with_content(content):
    # Zapisz zawartość do tymczasowego pliku
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sql", mode='w', encoding='utf-8') as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    # Otwórz edytor systemowy
    try:
        if os.name == 'nt':  # Windows
            os.startfile(tmp_path)
        elif os.name == 'posix':
            subprocess.call(['xdg-open', tmp_path])  # Linux
        else:
            subprocess.call(['open', tmp_path])  # Mac

        console.print(f"[bold blue]Edytuj plik, zapisz i naciśnij Enter tutaj, gdy skończysz...[/bold blue]")
        input()
    except Exception as e:
        console.print(f"[red]Nie udało się otworzyć edytora: {e}[/red]")

    # Odczytaj z powrotem zawartość
    with open(tmp_path, 'r', encoding='utf-8') as f:
        edited_content = f.read()

    os.remove(tmp_path)
    return edited_content


def process_file(file_path):
    console.print(f"\n[bold yellow]Plik:[/bold yellow] {file_path}")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    try:
        commented_sql = summarize_sql(content)
        console.print("\n[bold green]Wersja z komentarzami:[/bold green]\n")
        console.print(commented_sql)

        if Confirm.ask("Czy chcesz edytować komentarze przed zapisem?"):
            commented_sql = open_editor_with_content(commented_sql)

        if Confirm.ask("Czy zapisać jako -v2.sql?"):
            new_file = file_path.replace(".sql", "-v2.sql")
            with open(new_file, 'w', encoding='utf-8') as f:
                f.write(commented_sql)
            console.print(f"[green]Zapisano do:[/green] {new_file}")
        else:
            console.print("[red]Pominięto zapis.[/red]")
    except Exception as e:
        console.print(f"[red]Błąd przetwarzania pliku {file_path}: {e}[/red]")




def main():
    folder = Prompt.ask("Podaj ścieżkę do folderu z plikami SQL", default="../sql/to_do")
    if not os.path.exists(folder):
        console.print(f"[red]Folder {folder} nie istnieje.[/red]")
        return

    sql_files = [f for f in os.listdir(folder) if f.endswith('.sql')]
    if not sql_files:
        console.print("[yellow]Brak plików .sql w folderze.[/yellow]")
        return

    for file_name in sql_files:
        process_file(os.path.join(folder, file_name))

if __name__ == "__main__":
    main()
