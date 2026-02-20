/* ═══════════════════════════════════════════════════════════════
   🕌 Islamic Website — Main JavaScript Engine
   Theme, Audio Player, Bookmarks, Animations, PWA
   ═══════════════════════════════════════════════════════════════ */

// ── Theme Toggle ──────────────────────────────────────────────
function toggleTheme() {
    const html = document.documentElement;
    const current = html.getAttribute('data-theme');
    const next = current === 'dark' ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('theme', next);
    updateThemeIcon(next);
}

function updateThemeIcon(theme) {
    const icon = document.querySelector('.theme-icon');
    if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

// Restore theme on load
(function () {
    const saved = localStorage.getItem('theme') || 'dark';
    document.documentElement.setAttribute('data-theme', saved);
    document.addEventListener('DOMContentLoaded', () => updateThemeIcon(saved));
})();

// ── Mobile Menu ───────────────────────────────────────────────
function toggleMobileMenu() {
    const nav = document.getElementById('mobileMenu');
    if (nav) nav.classList.toggle('active');
}

// Close mobile nav on link click
document.addEventListener('DOMContentLoaded', function () {
    const mobileLinks = document.querySelectorAll('.mobile-menu a');
    mobileLinks.forEach(link => {
        link.addEventListener('click', () => {
            document.getElementById('mobileMenu')?.classList.remove('active');
        });
    });
});

// ── Audio Player ──────────────────────────────────────────────
let audioElement = null;
let isPlaying = false;

window.playAudio = function (url, title, subtitle) {
    const player = document.getElementById('audioPlayer');
    const playBtn = document.getElementById('playBtn');
    const titleEl = document.getElementById('audioTitle');
    const subEl = document.getElementById('audioSubtitle');
    const progressEl = document.getElementById('audioSeek');

    if (!audioElement) {
        audioElement = new Audio();
        audioElement.addEventListener('waiting', () => {
            if (playBtn) playBtn.classList.add('loading');
        });
        audioElement.addEventListener('playing', () => {
            if (playBtn) {
                playBtn.classList.remove('loading');
                playBtn.textContent = '⏸';
            }
        });
        audioElement.addEventListener('timeupdate', function () {
            if (audioElement.duration && progressEl) {
                progressEl.value = (audioElement.currentTime / audioElement.duration) * 100;
            }
        });
        audioElement.addEventListener('ended', function () {
            isPlaying = false;
            if (playBtn) playBtn.textContent = '▶';
            window.dispatchEvent(new Event('audioEnded'));
        });
    }

    audioElement.src = url;
    if (playBtn) playBtn.textContent = '⏳';
    audioElement.play().then(() => {
        isPlaying = true;
        if (playBtn) playBtn.textContent = '⏸';
    }).catch(e => {
        console.error("Audio play failed", e);
        if (playBtn) playBtn.textContent = '▶';
        if (typeof showToast === 'function') showToast('⚠️ تعذر تشغيل الصوت');
    });

    player.classList.add('active');
    if (titleEl) titleEl.textContent = title || '—';
    if (subEl) subEl.textContent = subtitle || '';
};

function togglePlay() {
    if (!audioElement) return;
    const playBtn = document.getElementById('playBtn');
    if (isPlaying) {
        audioElement.pause();
        isPlaying = false;
        playBtn.textContent = '▶';
    } else {
        audioElement.play();
        isPlaying = true;
        playBtn.textContent = '⏸';
    }
}

function seekAudio(val) {
    if (audioElement && audioElement.duration) {
        audioElement.currentTime = (val / 100) * audioElement.duration;
    }
}

function closePlayer() {
    if (audioElement) {
        audioElement.pause();
        audioElement.src = '';
    }
    isPlaying = false;
    document.getElementById('audioPlayer')?.classList.remove('active');
}

function nextAyah() {
    if (window.nextAyahCallback) window.nextAyahCallback();
}

function prevAyah() {
    if (window.prevAyahCallback) window.prevAyahCallback();
}

// ── Scroll Animations (Intersection Observer) ─────────────────
document.addEventListener('DOMContentLoaded', function () {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    // Observe cards and verse-cards for scroll animation
    document.querySelectorAll('.card, .verse-card, .hadith-card, .prayer-row').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(15px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });
});

// ── Service Worker Registration (PWA) ─────────────────────────
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function () {
        navigator.serviceWorker.register('/static/sw.js').catch(function () {
            // Service worker registration failed - not critical
        });
    });
}

// ── Keyboard Shortcuts ────────────────────────────────────────
document.addEventListener('keydown', function (e) {
    // Ctrl+K or Cmd+K → Focus search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const search = document.querySelector('.search-input');
        if (search) search.focus();
    }
    // Escape → Close mobile menu, audio player
    if (e.key === 'Escape') {
        document.getElementById('mobileMenu')?.classList.remove('active');
    }
    // Space → Toggle audio (only if not typing)
    if (e.key === ' ' && e.target.tagName !== 'INPUT' && e.target.tagName !== 'TEXTAREA') {
        if (audioElement && audioElement.src) {
            e.preventDefault();
            togglePlay();
        }
    }
});

// ── Toast Fallback (in case vip.js hasn't loaded yet) ─────────
if (typeof showToast === 'undefined') {
    window.showToast = function (msg) {
        const toast = document.createElement('div');
        toast.className = 'vip-toast slide-up';
        toast.textContent = msg;
        document.body.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    };
}
