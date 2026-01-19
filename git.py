import os
import json
import requests
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Check for API Keys
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not GITHUB_TOKEN or not GEMINI_API_KEY:
    print("⚠️  WARNING: API Keys missing in .env file.")

# ==========================================
# 1. GITHUB DATA FETCHING
# ==========================================

def fetch_user_repos(username: str) -> list:
    """Fetch all repository names for a GitHub user."""
    url = f"https://api.github.com/users/{username}/repos"
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            repos = response.json()
            return [repo["name"] for repo in repos]
        else:
            print(f"❌ Error fetching repos: {response.status_code} - {response.text}")
            return []
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return []

def fetch_language_stats(username: str) -> dict:
    """Fetch and calculate language usage percentages across all repos."""
    repo_names = fetch_user_repos(username)
    if not repo_names:
        return {}

    raw_languages = {}
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    print(f"🔄 Scanning {len(repo_names)} repositories for {username}...")

    for repo in repo_names:
        try:
            url = f"https://api.github.com/repos/{username}/{repo}/languages"
            response = requests.get(url, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                for lang, bytes_count in data.items():
                    raw_languages[lang] = raw_languages.get(lang, 0) + bytes_count
        except Exception:
            continue

    if not raw_languages:
        return {}

    # Calculate Percentages
    total_bytes = sum(raw_languages.values())
    final_stats = {k: round((v / total_bytes) * 100, 2) for k, v in raw_languages.items()}

    # Sort Descending
    return dict(sorted(final_stats.items(), key=lambda item: item[1], reverse=True))

# ==========================================
# 2. QUIZ GENERATION (AI)
# ==========================================

def generate_quiz_from_github(job_description: str, github_username: str) -> dict:
    """Generate a technical quiz based on JD and verified GitHub skills."""
    
    # 1. Get Real Data
    language_stats = fetch_language_stats(github_username)
    
    if not language_stats:
        return {"error": "No GitHub data found to generate quiz.", "quiz": None}

    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        
        prompt = f"""
        ### ROLE ###
        You are a Senior Technical Interviewer.
        
        ### DATA ###
        **Job Description:** "{job_description}"
        **Candidate's Verified Skills (GitHub):** {json.dumps(language_stats)}

        ### TASK ###
        Generate a 5-question multiple-choice quiz.
        
        ### RULES ###
        1. If JD requires a skill the candidate has (in GitHub stats), ask a **HARD** code-based question.
        2. If JD requires a skill the candidate LACKS, ask a **BASIC** conceptual question.
        3. Output ONLY valid JSON. No markdown formatting.
        
        ### JSON STRUCTURE ###
        [
          {{
            "question": "...",
            "options": ["A", "B", "C", "D"],
            "correct_option": "A",
            "category": "Coding" or "Theory",
            "reason": "Why this question was chosen"
          }}
        ]
        """

        response = client.models.generate_content(
            model="models/gemini-2.0-flash", # Updated to faster model if available, else use 1.5
            contents=prompt
        )

        # Clean Response (Remove Markdown if AI adds it)
        clean_text = response.text.strip().replace("```json", "").replace("```", "")
        quiz_data = json.loads(clean_text)

        return {"error": None, "quiz": quiz_data, "stats": language_stats}

    except Exception as e:
        return {"error": str(e), "quiz": None}

# ==========================================
# 3. SCORING LOGIC
# ==========================================

def calculate_github_score(github_username: str, job_description: str) -> float:
    """Calculate a relevance score (0-50) based on GitHub history."""
    stats = fetch_language_stats(github_username)
    if not stats: return 0.0

    jd_lower = job_description.lower()
    matches = sum(1 for lang in stats if lang.lower() in jd_lower)
    
    # Simple Scoring Logic
    base_points = min(20, len(stats) * 2)  # Max 20 for having diversity
    match_points = min(30, matches * 10)   # Max 30 for matching JD
    
    return float(base_points + match_points)

# ==========================================
# 4. MAIN EXECUTION (Console Output)
# ==========================================

if __name__ == "__main__":
    print("\n" + "="*40)
    print("   GITHUB SKILL VALIDATOR & QUIZ GEN   ")
    print("="*40)

    # 1. Inputs
    user = input(">>> Enter GitHub Username: ").strip()
    jd = input(">>> Enter Job Description: ").strip()

    print("\n[1/3] Fetching GitHub Data...")
    
    # 2. Generate Quiz
    result = generate_quiz_from_github(jd, user)

    # 3. Print Results
    if result.get("error"):
        print(f"\n❌ Error: {result['error']}")
    else:
        print(f"\n✅ Stats Found: {result['stats']}")
        print("\n" + "-"*40)
        print("         GENERATED QUIZ          ")
        print("-" * 40)
        
        quiz = result['quiz']
        for i, q in enumerate(quiz, 1):
            print(f"\nQ{i}: {q['question']}")
            print(f"   A) {q['options'][0]}")
            print(f"   B) {q['options'][1]}")
            print(f"   C) {q['options'][2]}")
            print(f"   D) {q['options'][3]}")
            print(f"   [Category: {q['category']}]")

    # 4. Calculate Score
    print("\n[3/3] Calculating Profile Score...")
    score = calculate_github_score(user, jd)
    print(f"\n🏆 GitHub Relevance Score: {score}/50")
    print("="*40 + "\n")