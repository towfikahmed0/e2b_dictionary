from bs4 import BeautifulSoup
import re
import requests
from requests.exceptions import RequestException
from concurrent.futures import ThreadPoolExecutor, as_completed
from colorama import init, Fore, Style
import json
import os
import time

# =======================
# CONFIG / CONSTANTS
# =======================
init(autoreset=True)

DICT_PATH = "dictionary.json"
GITHUB_DICT_URL = "https://raw.githubusercontent.com/towfikahmed0/Bornopath/refs/heads/main/dictionary.json"
MAX_WORKERS = 10

COMMON_WORDS = {
    'a', 'an', 'and', 'any', 'are', 'as', 'at', 'be', 'been', 'being', 'both',
    'but', 'by', 'can', 'each', 'every', 'few', 'for', 'from', 'he', 'her',
    'here', 'him', 'his', 'how', 'if', 'in', 'is', 'it', 'its', 'just',
    'many', 'me', 'more', 'most', 'much', 'my', 'no', 'not', 'of', 'on',
    'one', 'or', 'other', 'our', 'she', 'so', 'some', 'that', 'the', 'their',
    'them', 'there', 'these', 'they', 'this', 'too', 'to', 'us', 'very',
    'was', 'we', 'were', 'what', 'when', 'where', 'which', 'who', 'whom',
    'will', 'with', 'you', 'your', 'yes', 'while', 'three', 'four', 'five',
    'six', 'nine', 'ten', 'porn', 'fuck'
}

# =======================
# PRINT HELPERS
# =======================
def info(msg): print(Fore.CYAN + msg)
def warn(msg): print(Fore.YELLOW + msg)
def success(msg): print(Fore.GREEN + msg)
def error(msg): print(Fore.RED + msg)
def title(msg): print(Style.BRIGHT + Fore.MAGENTA + msg)


# =======================
# SESSION / DICTIONARY IO
# =======================
def create_session():
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/126.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    })
    return session


def load_dictionary(session=None):
    if os.path.exists(DICT_PATH):
        try:
            with open(DICT_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            info(f"> Loaded local dictionary with {len(data)} entries.")
            existing_set = {item.get('en', '').lower() for item in data if isinstance(item, dict)}
            return data, existing_set
        except Exception as e:
            warn(f"! Could not read local dictionary: {e}. Starting with empty dictionary.")
            return [], set()
    
    # Try to fetch from GitHub as fallback
    if session is None:
        session = create_session()
    try:
        resp = session.get(GITHUB_DICT_URL, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        with open(DICT_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        existing_set = {item.get('en', '').lower() for item in data if isinstance(item, dict)}
        success(f"> Downloaded dictionary from GitHub ({len(data)} entries).")
        return data, existing_set
    except Exception as e:
        warn(f"! Could not fetch dictionary from GitHub: {e}. Continuing with empty dictionary.")
        return [], set()


# =======================
# SIMPLE UTILITIES
# =======================
def ask_for_url():
    url = input("Enter the URL of the webpage: ").strip()
    if not url.startswith(("http://", "https://")):
        warn("Please enter a valid URL starting with http:// or https://")
        return ask_for_url()
    return url


def get_webpage(session, url):
    try:
        response = session.get(url, timeout=12)
        response.raise_for_status()
        return response.text
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            error("! Access forbidden — the website might be blocking bots.")
            warn("* Try changing the User-Agent or adding a small delay.")
        else:
            error(f"HTTP error: {e}")
    except RequestException as e:
        error(f"Error fetching the webpage: {e}")
    return None


def fetch_words_from_webpage(webpage):
    if webpage is None:
        warn("! No webpage content to process.")
        return []
    soup = BeautifulSoup(webpage, 'html.parser')
    text = soup.get_text(separator=' ')
    words = re.findall(r'\b[A-Za-z]+\b', text)
    unique_words = set(words)
    info(f"Found {len(unique_words)} unique alpha-only words.")
    return list(unique_words)


# =======================
# WORD FILTERING & CANDIDATES (IMPROVED)
# =======================
def generate_candidates(word):
    w = word.lower().strip()
    candidates = [w]
    
    # Only create base forms for words that are likely inflections
    base_forms = []
    
    # Handle common plural/verb patterns more carefully
    if w.endswith('ies') and len(w) > 4:
        base = w[:-3] + 'y'  # "studies" -> "study"
        if len(base) >= 3 and base.isalpha():
            base_forms.append(base)
    
    elif w.endswith('es') and len(w) > 3:
        # Only remove 'es' for specific patterns (avoid 'chang' from 'changes')
        base = w[:-2]
        if (len(base) >= 3 and base.isalpha() and 
            not base.endswith(('i', 'u', 'v', 's', 'x', 'z', 'h')) and
            base + 'e' not in COMMON_WORDS):  # Avoid 'chang' from 'changes'
            base_forms.append(base)
    
    elif w.endswith('s') and len(w) > 3 and not w.endswith(('ss', 'us', 'is', 'as')):
        base = w[:-1]
        if len(base) >= 3 and base.isalpha() and not base.endswith(('u', 'i')):
            base_forms.append(base)  # "books" -> "book"
    
    # Handle verb forms
    if w.endswith('ed') and len(w) > 4:
        base = w[:-2]
        if len(base) >= 3 and base.isalpha():
            base_forms.append(base)  # "worked" -> "work"
    
    if w.endswith('ing') and len(w) > 5:
        base = w[:-3]
        if len(base) >= 3 and base.isalpha():
            # Add 'e' back for words like "making" -> "make"
            if base.endswith(('k', 'm', 't', 'p', 'v')) and len(base) >= 4:
                base_with_e = base + 'e'
                if base_with_e.isalpha():
                    base_forms.append(base_with_e)  # "making" -> "make"
            else:
                base_forms.append(base)  # "going" -> "go"
    
    # Add base forms to candidates
    for base in base_forms:
        if base not in candidates and base not in COMMON_WORDS:
            candidates.append(base)
    
    return candidates


def filter_words(word_list, existing_words_set):

    out = set()
    for raw in word_list:
        w = raw.lower()
        if 3 < len(w) < 15 and w.isalpha() and w not in COMMON_WORDS and w not in existing_words_set:
            out.add(w)
    out_list = sorted(out)
    success(f"* Filtered down to {len(out_list)} candidate words after applying criteria.")
    return out_list


# =======================
# FETCH BANGLA MEANINGS (THREAD-SAFE)
# =======================
def get_word_bn(session, word_list):
    info(f"> Fetching Bangla meanings for {len(word_list)} words...")
    return_json = []

    def is_english_only(text):
        return bool(re.match(r'^[A-Za-z\s]+$', text))

    def process_bn_word(word):
        try:
            url = "https://www.english-bangla.com/dictionary/" + word
            response = session.get(url, timeout=8)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            bn_spans = soup.find_all("span", class_="format1")
            bn_list = []
            for span in bn_spans:
                text = span.get_text(separator=' ', strip=True)
                parts = re.split(r'[;,/]|(?:\s+or\s+)|(?:\s+and\s+)', text)
                for p in parts:
                    p = p.strip()
                    if p and not is_english_only(p) and len(p) <= 30:
                        bn_list.append(p)
            # fallback to single format1 if nothing captured
            if not bn_list and bn_spans:
                text = bn_spans[0].get_text(strip=True)
                if text and not is_english_only(text):
                    bn_list = [text]
            bn_list = list(dict.fromkeys(bn_list))[:5]
            if bn_list:
                return {'en': word, 'bn': bn_list}
        except Exception as e:
            return None
        return None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_bn_word, w) for w in word_list]
        for future in as_completed(futures):
            res = future.result()
            if res:
                return_json.append(res)

    success(f"> {len(return_json)} words with Bangla meanings fetched successfully.")
    return return_json


# =======================
# DICTIONARY.COM DETAILS (FIXED - CONSISTENT WORD USAGE)
# =======================
def get_definitions(session, word):
    try:
        # STEP 1: Validate word exists on dictionary.com
        dict_response = session.get("https://www.dictionary.com/browse/" + word, timeout=8)
        
        # If dictionary.com returns 404, word doesn't exist in proper form - REJECT
        if dict_response.status_code == 404:
            return None
        
        # STEP 2: Word exists, now get definitions from API
        resp = session.get(f"https://freedictionaryapi.com/api/v1/entries/en/{word}", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        
        definitions = []
        for entry in data["entries"]:
            for sense in entry["senses"]:
                definitions.append(sense["definition"])
        
        # Filter out plural definitions
        filtered_definitions = []
        for definition in definitions[0:5]:
            if not any(plural_indicator in definition.lower() for plural_indicator in 
                      ['plural of', 'pl. of', 'plural form of', 'pl form of']):
                filtered_definitions.append(definition)
        
        return filtered_definitions[:5] if filtered_definitions else None
        
    except Exception as e:
        return None


def get_synonyms(session, word):
    try:
        response = session.get("https://www.thesaurus.com/browse/" + word, timeout=8)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        meaning_divs = soup.find_all("div", class_="QXhVD4zXdAnJKNytqXmK")
        for meaning in meaning_divs:
            p_tags = meaning.find_all('p')
            for p in p_tags:
                if p.get_text() in ("Strongest matches", "Strong match", "Strong matches", "Strongest match"):
                    syn = meaning.find_all('a', class_="Bf5RRqL5MiAp4gB8wAZa")
                    syn = [s.get_text() for s in syn]
                    return [s for s in syn if s.strip()][:5]
    except Exception:
        return []
    return []


def get_antonyms(session, word):
    try:
        ant_url = f"https://api.datamuse.com/words?rel_ant={word}"
        ant_response = session.get(ant_url, timeout=8)
        ant_response.raise_for_status()
        antonyms = [w["word"] for w in ant_response.json()[:5]]
        return [a for a in antonyms if a.strip()]
    except Exception:
        return []
    return []


def get_bengali_for_single_word(session, word):

    try:
        bn_data = get_word_bn(session, [word])
        if bn_data and bn_data[0].get('bn'):
            return bn_data[0]['bn']
    except Exception:
        pass
    return []


def get_word_dtl(session, json_with_bn, existing_words_set):

    info("* Fetching detailed meanings for words...")
    dtl_array = []
    lock_seen = set()

    def try_word_with_details(word_to_try):
        """Helper to get English details for a specific word"""
        try:
            definitions = get_definitions(session, word_to_try)
            if definitions:
                return {
                    'en': word_to_try,
                    'def': definitions,
                    'syn': get_synonyms(session, word_to_try),
                    'ant': get_antonyms(session, word_to_try)
                }
        except Exception:
            return None
        return None

    def process_word(item):
        original_word = item.get('en', '').strip().lower()
        original_bn = item.get('bn', [])
        
        if not original_word:
            return None

        # Skip if already in dictionary
        if original_word in existing_words_set:
            return None

        # STEP 1: Try the ORIGINAL word first (perfect match scenario)
        original_result = try_word_with_details(original_word)
        if original_result:
            # Perfect match - use original Bangla meaning
            original_result['bn'] = original_bn
            return original_result

        # STEP 2: Try base forms with CONSISTENT Bengali fetching
        candidates = generate_candidates(original_word)
        for candidate in candidates:
            if candidate == original_word or candidate in existing_words_set:
                continue
                
            candidate_result = try_word_with_details(candidate)
            if candidate_result:
                # CRITICAL FIX: Always fetch Bengali for the EXACT candidate word
                candidate_bn = get_bengali_for_single_word(session, candidate)
                if candidate_bn:
                    candidate_result['bn'] = candidate_bn
                    success(f"✓ Consistent data for '{candidate}' (base form of '{original_word}')")
                    return candidate_result
                else:
                    # If no Bengali found for candidate, skip to avoid mismatches
                    warn(f"! No Bengali translation found for '{candidate}', skipping to avoid mismatch")
                    return None
        
        # No suitable candidate found
        return None

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = [executor.submit(process_word, item) for item in json_with_bn]
        for future in as_completed(futures):
            result = future.result()
            if result:
                en_lower = result['en'].lower()
                if en_lower not in lock_seen and en_lower not in existing_words_set:
                    lock_seen.add(en_lower)
                    dtl_array.append(result)

    success(f"> Detailed meanings fetched for {len(dtl_array)} words successfully.")
    return dtl_array


# =======================
# MAIN
# =======================
if __name__ == "__main__":
    banner = r'''
          _______  _______  ______   _______  _______ _________ _______           _______  _______ 
│╲     ╱│(  ___  )(  ____ )(  __  ╲ (  ____ ╲(  ____ ╲╲__   __╱(  ____ ╲│╲     ╱│(  ____ ╲(  ____ )
│ )   ( ││ (   ) ││ (    )││ (  ╲  )│ (    ╲╱│ (    ╲╱   ) (   │ (    ╲╱│ )   ( ││ (    ╲╱│ (    )│
│ │ _ │ ││ │   │ ││ (____)││ │   ) ││ (__    │ (__       │ │   │ │      │ (___) ││ (__    │ (____)│
│ │( )│ ││ │   │ ││     __)│ │   │ ││  __)   │  __)      │ │   │ │      │  ___  ││  __)   │     __)
│ ││ ││ ││ │   │ ││ (╲ (   │ │   ) ││ (      │ (         │ │   │ │      │ (   ) ││ (      │ (╲ (   
│ () () ││ (___) ││ ) ╲ ╲__│ (__╱  )│ )      │ (____╱╲   │ │   │ (____╱╲│ )   ( ││ (____╱╲│ ) ╲ ╲__
(_______)(_______)│╱   ╲__╱(______╱ │╱       (_______╱   )_(   (_______╱│╱     ╲│(_______╱│╱   ╲__╱
'''
    print(banner)
    info("- code by @towfikahmed07")

    session = create_session()
    existing_data, existing_words_set = load_dictionary(session)

    try:
        while True:
            url = ask_for_url()
            webpage = get_webpage(session, url)
            raw_words_list = fetch_words_from_webpage(webpage)
            final_words_list = filter_words(raw_words_list, existing_words_set)

            if not final_words_list:
                warn("No new candidate words after filtering. Try another URL or update the dictionary.")
            else:
                json_with_bn = get_word_bn(session, final_words_list)
                dtl_array = get_word_dtl(session, json_with_bn, existing_words_set)

                info(f"* Total words fetched with details: {len(dtl_array)}")

                # Merge with existing dictionary
                if os.path.exists(DICT_PATH):
                    try:
                        with open(DICT_PATH, "r", encoding="utf-8") as f:
                            existing_data = json.load(f)
                            existing_words_set = {item.get('en', '').lower() for item in existing_data if isinstance(item, dict)}
                    except Exception:
                        warn("! Could not re-read existing dictionary file — will attempt to merge anyway.")

                # Final merge: only add entries not present in existing_words_set
                new_entries = []
                for item in dtl_array:
                    en_lower = item['en'].lower()
                    if en_lower not in existing_words_set:
                        existing_data.append(item)
                        new_entries.append(item['en'])
                        existing_words_set.add(en_lower)

                if new_entries:
                    try:
                        with open(DICT_PATH, "w", encoding="utf-8") as f:
                            json.dump(existing_data, f, ensure_ascii=False, indent=4)
                        success(f"> Added {len(new_entries)} new words to {DICT_PATH}.")
                        success(f"> Words added: {', '.join(new_entries[:10])}{'...' if len(new_entries) > 10 else ''}")
                    except Exception as e:
                        error(f"! Failed to write dictionary file: {e}")
                else:
                    warn("> No new words to add. Dictionary is already up to date.")

            another = input("Do you want to fetch words from another URL? (y/n): ").strip().lower()
            if another != 'y':
                break

    except KeyboardInterrupt:
        warn("\nInterrupted by user. Exiting gracefully...")

    info("Exiting the program. Goodbye!")