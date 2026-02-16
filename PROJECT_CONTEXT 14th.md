# 100Days-to-UTME Project Context & Technical Specifications

## Project Overview
Automated JAMB UTME quiz platform with GitHub Actions workflow that generates quizzes every 2 days for 100-day study program.

**Start Date:** February 10, 2026  
**Duration:** 100 days (50 cycles of 2-day periods)  
**Target Users:** Nigerian JAMB UTME students

---

## Repository URLs

### Primary Repositories
- **Main Repo (Quiz Deployment):** https://github.com/artificialiman/100Days-to-UTME
- **Staging Repo (Question Upload):** https://github.com/artificialiman/Questt
- **Archive Repo (Permanent Storage):** https://github.com/artificialiman/Questt-resources

### Live Documentation
- **README (Workflow Specs):** https://raw.githubusercontent.com/artificialiman/100Days-to-UTME/refs/heads/main/README.md
- **Current UI Files:**
  - Landing page: https://raw.githubusercontent.com/artificialiman/100Days-to-UTME/refs/heads/main/index.html
  - Cluster selection: https://raw.githubusercontent.com/artificialiman/100Days-to-UTME/refs/heads/main/science_clusters.html
  - Quiz interface: https://raw.githubusercontent.com/artificialiman/100Days-to-UTME/refs/heads/main/quiz.html

---

## System Architecture

### 3-Repository Flow

```
┌─────────────────┐
│     Questt      │  ← You upload .txt files here every 2 days
│  (Staging Repo) │
└────────┬────────┘
         │
         │ GitHub Actions Workflow triggers
         ▼
┌─────────────────────────────────────────────────┐
│              Workflow Actions                   │
│  1. Validate .txt files                        │
│  2. Parse questions → JSON                     │
│  3. Generate HTML quizzes (embedded questions) │
│  4. Deploy to 100Days-to-UTME                  │
│  5. Archive to Questt-resources                │
│  6. Clear Questt repo                          │
└────────┬────────────────────────────────────────┘
         │
         ├─────────────────┬──────────────────┐
         ▼                 ▼                  ▼
┌─────────────────┐  ┌──────────────┐  ┌─────────────┐
│ 100Days-to-UTME │  │   Questt-    │  │   Questt    │
│  (Live Quizzes) │  │  resources   │  │  (Cleared)  │
│                 │  │  (Archive)   │  │             │
│ - quiz-*.html   │  │              │  │ (Empty -    │
│ - clusters      │  │ archive/     │  │  awaiting   │
│ - index.html    │  │  day-XX-YY/  │  │  next batch)│
└─────────────────┘  └──────────────┘  └─────────────┘
         │
         │ GitHub Pages deploys
         ▼
    Students access quizzes
```

---

## File Naming Conventions

### Question Files (Upload to Questt)
**Format:** `JAMB_{Subject}_Q1-35.txt`

**Required Files (Core Science):**
- `JAMB_Physics_Q1-35.txt`
- `JAMB_Mathematics_Q1-35.txt`
- `JAMB_English_Q1-35.txt`
- `JAMB_Chemistry_Q1-35.txt`

**Optional Files (Extended Clusters):**
- `JAMB_Biology_Q1-35.txt`
- `JAMB_Literature_Q1-35.txt`
- `JAMB_Government_Q1-35.txt`
- `JAMB_CRS_Q1-35.txt`
- `JAMB_Accounting_Q1-35.txt`
- `JAMB_Commerce_Q1-35.txt`
- `JAMB_Economics_Q1-35.txt`

### Question File Format (Inside .txt)
```
1. Question text here?
A. Option A
B. Option B
C. Option C
D. Option D
Answer: A

2. Next question?
A. Option A
B. Option B
C. Option C
D. Option D
Answer: C

[35 questions total per file]
```

### Generated Quiz Files (Auto-created by workflow)
**Individual Subjects:**
- `quiz-physics.html`
- `quiz-mathematics.html`
- `quiz-english.html`
- `quiz-chemistry.html`
- `quiz-biology.html`

**Cluster Quizzes (140 questions each):**
- `quiz-science-cluster-a.html` (Math + English + Physics + Chemistry)
- `quiz-science-cluster-b.html` (Biology + English + Physics + Chemistry)
- `quiz-arts-cluster-a.html` (English + Literature + Government + CRS)
- `quiz-commercial-cluster-a.html` (English + Accounting + Commerce + Economics)

---

## Workflow Trigger Conditions

### Automatic Triggers
1. **Scheduled:** Every 2 days at 3 AM (cron: `0 3 */2 * *`)
2. **Push Event:** When any `.txt` file uploaded to Questt repo main branch
3. **Manual:** Via GitHub Actions "Run workflow" button

### Day/Period Calculation
```python
current_date = datetime.now()
start_date = datetime(2026, 2, 10)
days_elapsed = (current_date - start_date).days
current_period = (days_elapsed // 2) + 1  # Period 1-50
day_range = f"Day {(current_period*2)-1}-{current_period*2}"

# Example:
# Feb 10 = Period 1, Day 1-2
# Feb 12 = Period 2, Day 3-4
# Feb 14 = Period 3, Day 5-6
```

---

## Validation Standards (Fail Gracefully Approach)

### File-Level Validation
- ✅ File exists and not empty
- ✅ UTF-8 encoding
- ✅ Reasonable file size (<5MB)

### Question-Level Validation
- ✅ Exactly 35 questions per file
- ✅ Question numbering 1-35 (no gaps, no duplicates)
- ✅ Four options (A, B, C, D) per question
- ✅ Answer key exists and matches A/B/C/D format
- ✅ No duplicate question text within file
- ✅ HTML-unsafe characters escaped (`<`, `>`, `&`, `"`)
- ✅ No empty question text or options
- ✅ Proper blank line formatting between questions

### Validation Behavior
**Fail Gracefully:**
- Invalid files logged to `validation-report.json`
- Valid files proceed to quiz generation
- Partial quizzes generated (only valid subjects)
- Students see warning banner for missing subjects

**Archive Structure:**
```
questt-resources/
  archive/
    day-01-02/
      JAMB_Physics_Q1-35.txt ✅
      JAMB_Mathematics_Q1-35.txt ✅
      JAMB_English_Q1-35.txt ❌ (validation failed)
      JAMB_Chemistry_Q1-35.txt ✅
      validation-report.json
      metadata.json
```

---

## Quiz HTML Template Requirements

### Core Features (Must Include)

#### 1. Fisher-Yates Option Randomization
```javascript
function shuffleOptions(question) {
    const options = [
        {label: 'A', text: question.optionA},
        {label: 'B', text: question.optionB},
        {label: 'C', text: question.optionC},
        {label: 'D', text: question.optionD}
    ];
    
    const correctAnswer = question.answer;
    
    // Fisher-Yates shuffle
    for (let i = options.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [options[i], options[j]] = [options[j], options[i]];
    }
    
    const newCorrectIndex = options.findIndex(opt => opt.label === correctAnswer);
    
    return {
        shuffledOptions: options,
        correctIndex: newCorrectIndex
    };
}
```

#### 2. Embedded Metadata
```html
<!-- Generated: Period 5, Day 9-10, 2026-02-26 -->
<!-- Validation: PASSED -->
<!-- Subjects: Physics, Mathematics, English, Chemistry -->
```

#### 3. Embedded Question Data
```javascript
window.quizData = [
    {
        id: 1,
        text: "Question text here?",
        optionA: "First option",
        optionB: "Second option",
        optionC: "Third option",
        optionD: "Fourth option",
        answer: "B"
    },
    // ... 35 questions total for individual subjects
    // ... 140 questions total for cluster quizzes
];

window.metadata = {
    period: 5,
    days: "9-10",
    subject: "Physics", // or "Science Cluster A"
    generatedDate: "2026-02-26",
    validationStatus: "PASSED", // or "PARTIAL"
    totalQuestions: 35
};
```

#### 4. Fallback Mechanism
```javascript
function showFallback() {
    const currentPeriod = calculateCurrentPeriod();
    const previousPeriod = currentPeriod - 1;
    
    displayNotification(`
        ⏳ Today's Quiz (Day ${currentPeriod*2-1}-${currentPeriod*2}) is Being Prepared
        
        Practicing yesterday's quiz while waiting.
        Check back in: 15 minutes
    `);
    
    // Load previous period's quiz
    loadPreviousQuiz(`quiz-${subject}-period-${previousPeriod}.html`);
}
```

#### 5. Partial Content Handling
```javascript
window.addEventListener('DOMContentLoaded', () => {
    // Validate question data
    if (!window.quizData || window.quizData.length === 0) {
        showFallback();
        return;
    }
    
    // Filter valid questions
    const validQuestions = window.quizData.filter(q => 
        q.text && q.optionA && q.optionB && q.optionC && q.optionD && q.answer
    );
    
    // Show warning if partial
    if (validQuestions.length < window.quizData.length) {
        showWarning(`⚠️ ${validQuestions.length}/${window.quizData.length} questions available`);
    }
    
    // Render valid questions only
    renderQuiz(validQuestions);
});
```

#### 6. Student-Facing Error Messages
```html
<div id="error-container" style="display:none;">
    <div class="error-banner">
        <i class="fas fa-exclamation-triangle"></i>
        <div>
            <h3>Quiz Temporarily Unavailable</h3>
            <p id="error-message"></p>
            <p>Try: Refresh page • Clear cache • Check back in 10 minutes</p>
        </div>
    </div>
</div>
```

### UI Components to Preserve
✅ Timer widget with progress ring  
✅ Calculator modal  
✅ Question navigator sidebar  
✅ Mobile bottom sheet palette  
✅ Submit confirmation modal  
✅ Current styling/animations  
✅ Flag/bookmark functionality  

---

## GitHub Secrets Configuration

### Required Secret
**Name:** `WORKFLOW_TOKEN`  
**Type:** GitHub Personal Access Token (Classic)  
**Scopes:**
- ✅ `repo` (Full control of private repositories)
- ✅ `workflow` (Update GitHub Action workflows)

**Permissions Needed:**
- Read from Questt repo
- Write to 100Days-to-UTME repo
- Write to Questt-resources repo

**Location:** 100Days-to-UTME repo → Settings → Secrets and variables → Actions

---

## Files to Create

### 1. `validate_questions.py`
**Location:** 100Days-to-UTME repo root  
**Purpose:** Validate .txt files against standards  
**Outputs:** `validation-report.json`

### 2. `parser.py`
**Location:** 100Days-to-UTME repo root  
**Purpose:** Parse .txt files → JSON array for HTML embedding

### 3. `quiz-template.html`
**Location:** 100Days-to-UTME repo root  
**Purpose:** Base template for all generated quiz files  
**Includes:**
- Fisher-Yates shuffle
- Fallback mechanism
- Error handling
- Metadata placeholders
- Question data placeholder

### 4. `.github/workflows/auto-quiz.yml`
**Location:** 100Days-to-UTME repo `.github/workflows/`  
**Purpose:** Main automation workflow

**Workflow Steps:**
```yaml
1. Checkout Questt repo
2. Validate .txt files (validate_questions.py)
3. Parse questions (parser.py)
4. Generate HTML files (embed questions in template)
5. Add Fisher-Yates + fallback logic
6. Commit to 100Days-to-UTME
7. Archive to Questt-resources with validation report
8. Clear Questt repo
```

### 5. Updated `index.html`
**Changes:**
- Add day/period tracker widget
- Show "Day X-Y Available" status
- Link to current period's quizzes

### 6. Updated cluster pages
**Files:** `science_clusters.html`, `art_clusters.html`, `commercial_clusters.html`  
**Changes:**
- Point buttons to generated quiz files (not generic quiz.html)
- Add quiz availability checker

---

## UI Flow (Updated)

```
1. Student visits index.html
   ↓
2. Sees "Day 9-10 Available" (calculated dynamically)
   ↓
3. Selects stream (Science/Arts/Commercial)
   ↓
4. Redirected to {stream}_clusters.html
   ↓
5. Selects cluster (e.g., Science Cluster A)
   ↓
6. Clicks "Start Practice Test"
   ↓
7. Button links to: quiz-science-cluster-a.html
   ↓
8. Quiz loads:
   - If questions exist → Render with Fisher-Yates shuffle
   - If partial questions → Show warning + valid questions
   - If no questions → Load previous day's quiz + waiting notice
   ↓
9. Student completes quiz
   ↓
10. Submit → See results
```

---

## Student Experience Scenarios

### Scenario A: All Valid (Happy Path)
- Student sees complete quiz (all subjects in cluster)
- 140 questions with randomized options
- Timer starts at 60 minutes (for cluster)
- Can navigate, flag, submit normally

### Scenario B: Partial Validation Failure
- Warning banner: "⚠️ Mathematics quiz unavailable. Practice available subjects."
- Shows Physics, English, Chemistry only (105 questions)
- Timer adjusts proportionally
- Can still submit and get score

### Scenario C: Complete Failure (Worst Case)
- Automatically loads Day 7-8 quiz
- Notice: "⏳ Day 9-10 quiz being prepared. Practice Day 7-8 while waiting."
- Auto-refresh prompt after 15 minutes
- No blank screens, professional UX

---

## Technical Decisions Made

### ✅ Confirmed Choices
1. **Validation:** Fail gracefully (partial quizzes OK)
2. **Randomization:** Fisher-Yates algorithm
3. **Error Handling:** Show partial content with warnings
4. **Fallback:** Display previous day's quiz automatically
5. **Question Format:** Embedded JSON in HTML (not separate files)
6. **UI Preservation:** Keep all current components (timer, calculator, navigator)

### ⏳ Pending Decisions
- None (all major decisions finalized)

---

## Development Status

### ✅ Completed
- Repository structure defined
- GitHub token and secrets configured
- Technical specifications documented
- Validation standards defined
- UI flow mapped

### 🚧 In Progress
- Creating workflow files
- Building validation script
- Creating quiz template

### 📋 Todo
- Test workflow with sample questions
- Deploy to GitHub Pages
- Create day tracker widget
- Update cluster selection pages
- Generate first batch of quizzes (Day 1-2)

---

## Manual Operations Required

### Every 2 Days (Your Responsibility)
1. Receive notification: "Questt repo cleared"
2. Upload new `.txt` files to Questt repo via GitHub web:
   - Day 3-4 questions on Feb 12
   - Day 5-6 questions on Feb 14
   - Continue for 50 cycles
3. Workflow triggers automatically (or at 3 AM)
4. Verify deployment successful
5. Test at least one quiz

### One-Time Setup
- ✅ Create 3 repositories
- ✅ Generate GitHub token
- ✅ Add token as secret
- ⏳ Create workflow file
- ⏳ Upload quiz template
- ⏳ Upload validation/parser scripts

---

## Success Metrics

**System is working correctly when:**
- ✅ Workflow runs every 2 days without errors
- ✅ Quizzes deploy to GitHub Pages within 2 minutes
- ✅ Students see updated quizzes every 2 days
- ✅ Invalid questions logged but don't break system
- ✅ Partial quizzes display gracefully
- ✅ Questt repo auto-clears after processing
- ✅ All questions archived to Questt-resources
- ✅ Zero manual HTML editing required

---

## Known Limitations

1. **No rollback mechanism** - Manual fix if bad quiz deployed
2. **No email notifications** - Must check Actions tab for errors
3. **GitHub Pages delay** - 1-10 minutes for deployment
4. **Manual uploads only** - No bulk scheduling (intentional)
5. **Free tier limits** - 2,000 minutes/month (well within budget)

---

## Cost Analysis

**GitHub Actions:** FREE  
- 2,000 minutes/month included
- Workflow uses ~2 minutes per run
- 50 runs over 100 days = 100 minutes total

**GitHub Pages:** FREE  
**Repository Storage:** FREE (within limits)

**Total Cost:** $0

---

## Contact & Support

**Repository Owner:** artificialiman  
**Project Type:** Educational/Open Source  
**Support:** Via GitHub Issues on 100Days-to-UTME repo

---

## Next Agent Instructions

**If you're picking up this project:**

1. Read this entire context document
2. Review the README at the URL provided
3. Check current UI files (URLs above)
4. Continue from "Development Status - In Progress" section
5. Create files in order listed in "Files to Create"
6. Test workflow before launch date (Feb 10, 2026)
7. Maintain same technical decisions and architecture
8. Preserve existing UI components and styling
9. Keep communication concise and technical
10. Ask for clarification before deviating from specs

**Key Principle:** Fail gracefully, show partial content, always provide fallback to students.

---

*Document Last Updated: 2026-02-16*  
*Version: 1.0*  
*Status: Active Development*
