# 📋 Daily Planner

A personal daily planner built as a single HTML file — no frameworks, no backend, no dependencies. Just open it in any browser and start planning.

---

## ✨ Features

- **📅 Daily Schedule** — Pre-loaded time blocks from 4:00 AM to 10:00 PM
- **✅ Task Completion** — Check off tasks with a single click
- **🎨 Color-Coded Status** — Visual indicators for current, done, missed, and upcoming tasks
- **⏱ Live Clock** — Real-time clock with automatic slot highlighting
- **💾 Auto-Save** — All changes saved instantly in browser localStorage (persists after closing)
- **📂 History Log** — Save completed days and review past performance anytime
- **📊 Progress Tracker** — Live stats bar showing total / done / missed / upcoming counts
- **📝 Notes Section** — Freeform notes area for ideas and reminders
- **➕ Custom Time Blocks** — Add extra slots beyond the default schedule
- **📱 Responsive** — Works on desktop and mobile browsers

---

## 🚀 Getting Started

### Option 1 — Open Directly
Just download `daily-planner.html` and open it in any browser. No setup needed.

### Option 2 — Clone the Repo
```bash
git clone https://github.com/your-username/daily-planner.git
cd daily-planner
open daily-planner.html
```

> No `npm install`, no build step, no server required.

---

## 🗂 File Structure

```
daily-planner/
│
├── daily-planner.html     # The entire app — HTML, CSS, and JS in one file
└── README.md              # You're reading it
```

---

## 🧠 How It Works

| Feature | Implementation |
|---|---|
| Persistence | Browser `localStorage` keyed by date |
| Auto-save | Fires on every input/change event |
| Color coding | Time-based state computed each minute |
| History | JSON array stored in `localStorage` under `planner_hist` |
| No internet needed | Google Fonts loaded via CDN (fallback to system fonts if offline) |

---

## 📖 Usage Guide

### Checking Off Tasks
Click the **circle button** on the right of any task row. It turns green and the task is crossed out.

### Saving Your Day to History
Click **💾 Save Day** at the bottom. Then switch to the **📂 History tab** to review past days.

### Adding Custom Time Blocks
Click **+ Add time block** below the schedule, enter a time and task description.

### Clearing the Day
Click **Clear** at the bottom footer to reset today's entries.

---

## 🛠 Customization

To personalize the default schedule, open `daily-planner.html` and edit the `DEFAULTS` array in the `<script>` section:

```js
const DEFAULTS = [
  { time: '6:00 AM', val: 'Morning run' },
  { time: '7:00 AM', val: 'Breakfast' },
  // add your own slots here
];
```

To change the color theme, update the CSS variables at the top of the `<style>` section:

```css
:root {
  --accent: #c8440a;       /* primary accent color */
  --done-border: #7aaa5a;  /* done/green color */
  --missed-border: #d94040; /* missed/red color */
}
```

---

## 💡 Tips

- **Bookmark** the file in your browser for one-click access every morning
- **Keep the same file** — your history is stored in that browser's localStorage
- If you want to **migrate data** between devices, use the browser DevTools console to export/import `localStorage` entries
- Works fully **offline** (except Google Fonts — fallback fonts load automatically)

---

## 📸 Preview

> *(Add a screenshot of your planner here)*
> `![Planner Preview](screenshot.png)`

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

## 🙌 Author

Built for personal productivity tracking.  
Feel free to fork and adapt it to your own daily routine.
