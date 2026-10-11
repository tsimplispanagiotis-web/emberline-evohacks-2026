# EVO HACKS 2026 — ΟΔΗΓΙΕΣ ΥΠΟΒΟΛΗΣ EMBERLINE 3.0

## ΠΡΟΘΕΣΜΙΑ

**11 Οκτωβρίου 2026, 11:59 π.μ. PDT = 21:59 ώρα Ελλάδας.** Το banner του Devpost γράφει 12:00 PDT· για ασφάλεια υποβολή πριν τις **21:30 ώρα Ελλάδας**. Οι διοργανωτές ζητούν δημόσιο source repository, demo video **2–3 λεπτών**, περιγραφή και link εφαρμογής ή οδηγίες τοπικής εκτέλεσης.

Επίσημες οδηγίες: https://evohackathon2026.devpost.com/ και https://evohackathon2026.devpost.com/rules

## 1. GitHub — ο κώδικας

1. Κατέβασε το **EMBERLINE_3_0_SOURCE_GITHUB_READY.zip** και αποσυμπίεσε.
2. Άνοιξε https://github.com/new (κάνε σύνδεση/εγγραφή). Διάλεξε **Repository name:** `emberline-evohacks-2026`, **Public** και **Create repository**. Μην αρχικοποιήσεις δεύτερο README ή `.gitignore`, επειδή υπάρχουν ήδη.
3. Στη νέα άδεια σελίδα, επέλεξε **uploading an existing file** (ή **Add file → Upload files**). Κάνε drag-and-drop **τα περιεχόμενα** του αποσυμπιεσμένου φακέλου: `app/`, `tests/`, `README.md`, `requirements.txt`, `Dockerfile`, `benchmark.py`, `evaluate_model.py`, `start_*.sh/bat` κ.ά. **Όχι μόνο το ZIP.** Το `README.md` πρέπει να εμφανιστεί στη ρίζα του repo.
4. Πάτα **Commit changes**. Αν δεν περάσουν οι υποφάκελοι με τον browser, χρησιμοποίησε GitHub Desktop (File → Add Local Repository → Create repository here → Publish repository ως Public) ή το Git CLI.
5. Άνοιξε το repo σε ανώνυμη περιήγηση και βεβαιώσου ότι βλέπεις τα αρχεία. Αντιγράφεις το πραγματικό URL, π.χ. `https://github.com/TO_USERNAME_SOU/emberline-evohacks-2026` (αντικατάστησε οπωσδήποτε το username).

**Προσοχή:** Δεν περιλαμβάνουμε `emberline.sqlite3`, API keys, προσωπικά δεδομένα ή το μεγάλο raw recording. Η έκδοση είναι δημιουργημένη στον χρόνο του hackathon (10–11 Οκτωβρίου).

## 2. YouTube — το βίντεο

1. Από το **FULL_SUBMISSION_KIT** άνοιξε `media/EMBERLINE_v3_EvoHacks_Demo.mp4`.
2. Άνοιξε https://studio.youtube.com/ → **Create → Upload videos**. Ανέβασε το MP4.
3. **Title:** `EMBERLINE 3.0 | AI Triage, Exact Optimization & Resilience Lab | EvoHacks 2026`.
4. **Visibility:** Unlisted (όποιος έχει το link το βλέπει). Όχι Private. Αν το YouTube επιβάλει διαφορετικά όρια/επαλήθευση, ολοκλήρωσέ τα πριν την προθεσμία.
5. Αντίγραψε το **πραγματικό** URL και δοκίμασέ το σε ανώνυμη περιήγηση. Βεβαιώσου ότι διαρκεί **2–3 λεπτά**, ότι παίζει με ήχο και ότι οι λεζάντες φαίνονται.

## 3. Devpost — υποβολή

1. https://evohackathon2026.devpost.com/ → **Join hackathon** (εφόσον δεν έχει γίνει ήδη) → **Submit a project** / **My projects** → νέα υποβολή.
2. **Project name:** `EMBERLINE 3.0 — From Chaos to Coordinated Action`.
3. **Tagline:** `Multilingual AI triage meets exact resource optimization and what-if resilience planning — with humans in control.`
4. Για **Inspiration / What it does / How we built it / Challenges / Accomplishments / What we learned / What's next** αντέγραψε τα αντίστοιχα πεδία από `DEVPOST_SUBMISSION.md` (είναι στα αγγλικά, έτοιμα).
5. **Built with:** `Python, FastAPI, scikit-learn, SciPy, HiGHS, SQLite, JavaScript, CSS, pytest`.
6. **Video URL:** το πραγματικό YouTube link. **Repository:** το πραγματικό δημόσιο GitHub link. **App/build:** οι οδηγίες του GitHub README ή το `start_mac_linux.sh` / `start_windows.bat`. Μην χρησιμοποιήσεις το παλιό Lovable preview ως δήθεν deployment της FastAPI έκδοσης.
7. Προαιρετικά ανέβασε screenshot `media/EMBERLINE_v3_ResilienceLab.png` ως cover, καθώς και `EMBERLINE2_Reasoning.png` για AI explainability.
8. Πάτα **Submit**, ΟΧΙ μόνο Save Draft. Επιβεβαίωσε ότι φαίνεται στο Devpost ως **submitted** και ότι τα δύο URL λειτουργούν εκτός λογαριασμού.

## 4. Έλεγχος κριτών — τι δείχνουμε

Το project επεξεργάζεται **11 συνθετικά μηνύματα**, βρίσκει **1 πιθανή διπλοεγγραφή**, κρατάει **1 κρίσιμο περιστατικό για ανθρώπινη εξέταση** και συνθέτει **8 εφικτές προτάσεις** με 0–1 MILP. Στο **Scenario Lab** δείξε **Food shortage** (8→7) και **Volunteer absence** (ίδιο πλήθος 8 αλλά 3 επαναναθέσεις). Καμία από αυτές τις προσομοιώσεις δεν ξοδεύει πόρους. Οι ανθρώπινες εγκρίσεις δεσμεύουν τους *συνθετικούς* πόρους και αναδημιουργούν εφικτό πλάνο.

`python -m pytest -q` → **143 passed**, συμπεριλαμβανομένων **80 μικρών τυχαίων προβλημάτων όπου η έξοδος MILP συμφωνεί με ανεξάρτητη εξαντλητική αναζήτηση**. `python evaluate_model.py` → **78.6% synthetic in-domain 5-fold CV**. Αυτές είναι δοκιμές του διαγωνιστικού prototype, **όχι** αποτελέσματα σε αληθινές καταστροφές ή εγγύηση ασφαλείας.

## 5. Εάν έχεις μόνο κινητό

Κατέβασε το **source ZIP**, αποσυμπίεσέ το στην εφαρμογή Αρχεία και άνοιξε GitHub με «Αίτημα ιστότοπου για υπολογιστές» αν δεν εμφανίζεται η επιλογή upload. Η μεταφορά πολλών υποφακέλων μέσω browser σε iPhone μπορεί να είναι δύσκολη· προτίμησε υπολογιστή/GitHub Desktop, εφόσον διαθέτεις. Μην ανεβάσεις μόνο ένα ZIP ως μοναδικό αρχείο στο repository.

**Τελευταίο:** αποθηκευμένο draft ≠ υποβλημένο project. Κάνε έλεγχο πριν τις 21:59.
