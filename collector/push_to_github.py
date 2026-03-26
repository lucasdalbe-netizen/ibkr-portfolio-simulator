import os
import json
import base64
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_API = "https://api.github.com"

def get_file_sha(path):
    """Récupère le SHA du fichier sur GitHub (nécessaire pour le mettre à jour)"""
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["sha"]
    return None  # fichier n'existe pas encore

def push_file(local_path, remote_path, commit_message):
    """Push un fichier local vers GitHub"""
    with open(local_path, "rb") as f:
        content = base64.b64encode(f.read()).decode("utf-8")

    sha = get_file_sha(remote_path)
    url = f"{GITHUB_API}/repos/{GITHUB_REPO}/contents/{remote_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": commit_message,
        "content": content,
    }
    if sha:
        payload["sha"] = sha  # obligatoire pour update un fichier existant

    response = requests.put(url, headers=headers, json=payload)

    if response.status_code in [200, 201]:
        print(f"Pushé avec succès : {remote_path}")
    else:
        print(f"Erreur push {remote_path} : {response.status_code} — {response.text}")

def push_all_snapshots(local_dir="data/realtime"):
    for filename in os.listdir(local_dir):
        if filename.endswith(".json"):
            local_path = os.path.join(local_dir, filename)
            remote_path = f"data/realtime/{filename}"
            push_file(local_path, remote_path, f"Update snapshot {filename}")

def push_all_historical(local_dir="data/historical"):
    for filename in os.listdir(local_dir):
        if filename.endswith(".csv"):
            local_path = os.path.join(local_dir, filename)
            remote_path = f"data/historical/{filename}"
            push_file(local_path, remote_path, f"Update historical {filename}")

if __name__ == "__main__":
    print("Push des snapshots temps réel...")
    push_all_snapshots()

    print("Push des données historiques...")
    push_all_historical()

    print("Tout pushé sur GitHub.")
