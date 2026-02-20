/**
 * 🕌 QURAN VIP — Advanced Features Engine
 * Handles Reading Progress, Streaks, Custom Modals, and Gamification.
 */

document.addEventListener('DOMContentLoaded', () => {
    initReadingProgress();
    initDailyStreak();
    replaceNativeAlerts();
    initPrayerTimeChecker();
    initAdhkar();
});

/* ═══════════════════════════════════════════════════════════════
   📊 READING PROGRESS TRACKER
   ═══════════════════════════════════════════════════════════════ */
function initReadingProgress() {
    // Check if we are on a Surah page
    if (!window.location.pathname.includes('/quran/')) return;

    const surahId = parseInt(window.location.pathname.split('/').pop());
    if (isNaN(surahId)) return;

    // Track scroll to mark verses as read (simplified logic)
    let maxRead = 0;
    window.addEventListener('scroll', () => {
        const verses = document.querySelectorAll('.verse-card');
        verses.forEach(v => {
            const rect = v.getBoundingClientRect();
            if (rect.top >= 0 && rect.bottom <= window.innerHeight) {
                const ayahNum = parseInt(v.dataset.ayah);
                if (ayahNum > maxRead) {
                    maxRead = ayahNum;
                    saveProgress(surahId, maxRead);
                }
            }
        });
    });
}

function saveProgress(surah, ayah) {
    let progress = JSON.parse(localStorage.getItem('quran_progress') || '{}');
    // Only update if further ahead
    if (!progress[surah] || progress[surah] < ayah) {
        progress[surah] = ayah;
        localStorage.setItem('quran_progress', JSON.stringify(progress));
        updateStreak();
    }
}

/* ═══════════════════════════════════════════════════════════════
   🔥 DAILY STREAK SYSTEM
   ═══════════════════════════════════════════════════════════════ */
function initDailyStreak() {
    const lastVisit = localStorage.getItem('last_visit_date');
    const today = new Date().toISOString().split('T')[0];
    let streak = parseInt(localStorage.getItem('reading_streak') || '0');

    if (lastVisit !== today) {
        if (isYesterday(lastVisit)) {
            // Continued streak — don't increment yet, wait for reading action
        } else {
            // Broken streak, reset if not first time
            if (lastVisit) streak = 0;
        }
        localStorage.setItem('last_visit_date', today);
        localStorage.setItem('reading_streak', streak);
    }

    // Display streak if > 0
    if (streak > 0) {
        showToast(`🔥 يوم ${streak} على التوالي!`);
    }
}

function updateStreak() {
    const today = new Date().toISOString().split('T')[0];
    const lastRead = localStorage.getItem('last_read_date');

    if (lastRead !== today) {
        let streak = parseInt(localStorage.getItem('reading_streak') || '0');
        streak++;
        localStorage.setItem('reading_streak', streak);
        localStorage.setItem('last_read_date', today);
        showToast(`🎉 رائع! زد رصيدك إلى ${streak} أيام!`);
    }
}

function isYesterday(dateStr) {
    if (!dateStr) return false;
    const date = new Date(dateStr);
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return date.toISOString().split('T')[0] === yesterday.toISOString().split('T')[0];
}

/* ═══════════════════════════════════════════════════════════════
   🛡️ CUSTOM MODALS (Replacing Alerts)
   ═══════════════════════════════════════════════════════════════ */
function replaceNativeAlerts() {
    window.alert = function (msg) {
        showCustomModal(msg, 'alert');
    };

    // Hook into geolocation permission request
    const prayerPage = document.querySelector('.prayer-times-page');
    if (prayerPage && !localStorage.getItem('geo_permission')) {
        showCustomModal('نود معرفة موقعك لعرض مواقيت الصلاة بدقة. هل تسمح؟', 'confirm', () => {
            localStorage.setItem('geo_permission', 'asked');
            if (window.getPrayerTimes) window.getPrayerTimes();
        });
    }
}

function showCustomModal(msg, type = 'alert', callback = null) {
    const container = document.getElementById('vip-modal-container');
    if (!container) return;

    const modal = document.createElement('div');
    modal.className = 'vip-modal-overlay fade-in';
    modal.innerHTML = `
        <div class="vip-modal slide-up">
            <div class="vip-modal-icon">${type === 'confirm' ? '📍' : '✨'}</div>
            <div class="vip-modal-content">${msg}</div>
            <div class="vip-modal-actions">
                ${type === 'confirm'
            ? `<button class="btn btn-secondary" onclick="closeModal(this)">لاحقاً</button>
                       <button class="btn btn-primary" id="confirmData">موافق</button>`
            : `<button class="btn btn-primary" onclick="closeModal(this)">حسناً</button>`
        }
            </div>
        </div>
    `;

    container.innerHTML = '';
    container.appendChild(modal);

    if (type === 'confirm' && callback) {
        document.getElementById('confirmData').onclick = () => {
            closeModal(modal.querySelector('.vip-modal'));
            callback();
        };
    }
}

function closeModal(btn) {
    const overlay = btn.closest('.vip-modal-overlay');
    if (!overlay) return;
    overlay.style.opacity = '0';
    setTimeout(() => overlay.remove(), 300);
}

function showToast(msg) {
    const toast = document.createElement('div');
    toast.className = 'vip-toast';
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

/* ═══════════════════════════════════════════════════════════════
   ⏰ PRAYER TIME CHECKER
   ═══════════════════════════════════════════════════════════════ */
function initPrayerTimeChecker() {
    // Check every 60 seconds if it's prayer time
    setInterval(() => {
        const cached = localStorage.getItem('cached_prayer_times');
        if (!cached) return;

        try {
            const times = JSON.parse(cached);
            const now = new Date();
            const nowStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;

            const prayerNames = {
                'Fajr': 'الفجر',
                'Dhuhr': 'الظهر',
                'Asr': 'العصر',
                'Maghrib': 'المغرب',
                'Isha': 'العشاء'
            };

            for (const [key, name] of Object.entries(prayerNames)) {
                if (times[key] && times[key].substring(0, 5) === nowStr) {
                    showToast(`🕌 حان الآن موعد صلاة ${name}`);
                    break;
                }
            }
        } catch (e) {
            // Silently ignore parse errors
        }
    }, 60000);
}

/* ═══════════════════════════════════════════════════════════════
   📿 ADHKAR COUNTER SYSTEM
   ═══════════════════════════════════════════════════════════════ */
function initAdhkar() {
    if (!window.location.pathname.includes('/adhkar')) return;

    // Restore counts from localStorage
    const saved = JSON.parse(localStorage.getItem('dhikr_progress') || '{}');
    const today = new Date().toISOString().split('T')[0];

    // Reset if new day
    if (saved.date !== today) {
        localStorage.setItem('dhikr_progress', JSON.stringify({ date: today, counts: {} }));
        return;
    }

    // Apply saved counts
    if (saved.counts) {
        Object.keys(saved.counts).forEach(id => {
            const card = document.getElementById(id);
            if (card) {
                const count = saved.counts[id];
                const ring = card.querySelector('.counter-ring');
                if (!ring) return;
                const total = parseInt(ring.dataset.total);

                ring.dataset.current = count;
                const percentage = (count / total) * 100;
                const circle = ring.querySelector('.circle');
                if (circle) circle.setAttribute('stroke-dasharray', `${percentage}, 100`);
                const counterText = ring.querySelector('.counter-text');
                if (counterText) counterText.innerText = count >= total ? '✓' : (total - count);

                if (count >= total) {
                    card.classList.add('completed');
                }
            }
        });
    }
}

// Hook into the inline onclick in HTML to save progress
window.saveDhikrProgress = function (cardId, currentCount) {
    const saved = JSON.parse(localStorage.getItem('dhikr_progress') || JSON.stringify({ date: new Date().toISOString().split('T')[0], counts: {} }));
    saved.counts[cardId] = currentCount;
    localStorage.setItem('dhikr_progress', JSON.stringify(saved));
};
