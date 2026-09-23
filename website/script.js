/* ════════════════════════════════════════════
   TWEAKIFY — Landing Page JavaScript
   ════════════════════════════════════════════ */

// ── Animated Background (Grid + Particles) ──
(function () {
  const canvas = document.getElementById('bg-canvas');
  const ctx = canvas.getContext('2d');
  let W, H, particles = [], animId;

  const ACCENT = '#00d4ff';
  const GREEN = '#00ff88';

  function resize() {
    W = canvas.width = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  // Grid lines
  function drawGrid() {
    ctx.strokeStyle = 'rgba(0, 212, 255, 0.04)';
    ctx.lineWidth = 1;
    const step = 60;
    for (let x = 0; x <= W; x += step) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y <= H; y += step) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }
  }

  // Particles
  class Particle {
    constructor() { this.reset(); }
    reset() {
      this.x = Math.random() * W;
      this.y = Math.random() * H;
      this.r = Math.random() * 1.8 + 0.3;
      this.vx = (Math.random() - 0.5) * 0.35;
      this.vy = (Math.random() - 0.5) * 0.35;
      this.a = Math.random() * 0.6 + 0.2;
      this.c = Math.random() > 0.5 ? ACCENT : GREEN;
    }
    update() {
      this.x += this.vx;
      this.y += this.vy;
      if (this.x < 0 || this.x > W || this.y < 0 || this.y > H) this.reset();
    }
    draw() {
      ctx.beginPath();
      ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2);
      ctx.fillStyle = this.c.replace(')', `, ${this.a})`).replace('rgb', 'rgba').replace('#00d4ff', `rgba(0,212,255,${this.a})`).replace('#00ff88', `rgba(0,255,136,${this.a})`);
      ctx.fill();
    }
  }

  function initParticles(n = 90) {
    particles = Array.from({ length: n }, () => new Particle());
  }
  initParticles();

  // Connect nearby particles
  function connectParticles() {
    const maxDist = 110;
    for (let i = 0; i < particles.length; i++) {
      for (let j = i + 1; j < particles.length; j++) {
        const dx = particles[i].x - particles[j].x;
        const dy = particles[i].y - particles[j].y;
        const d = Math.sqrt(dx * dx + dy * dy);
        if (d < maxDist) {
          const alpha = (1 - d / maxDist) * 0.12;
          ctx.beginPath();
          ctx.strokeStyle = `rgba(0, 212, 255, ${alpha})`;
          ctx.lineWidth = 0.5;
          ctx.moveTo(particles[i].x, particles[i].y);
          ctx.lineTo(particles[j].x, particles[j].y);
          ctx.stroke();
        }
      }
    }
  }

  function loop() {
    ctx.clearRect(0, 0, W, H);
    drawGrid();
    connectParticles();
    particles.forEach(p => { p.update(); p.draw(); });
    animId = requestAnimationFrame(loop);
  }
  loop();
})();


// ── Navbar scroll effect ──
const navbar = document.getElementById('navbar');
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 60);
});


// ── Hamburger menu ──
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobile-menu');
let menuOpen = false;

hamburger.addEventListener('click', () => {
  menuOpen = !menuOpen;
  mobileMenu.classList.toggle('open', menuOpen);
});

document.querySelectorAll('.mobile-link').forEach(link => {
  link.addEventListener('click', () => {
    menuOpen = false;
    mobileMenu.classList.remove('open');
  });
});


// ── Smooth scroll for nav links ──
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  });
});


// ── Animated counters ──
function animateCounter(el) {
  const target = +el.dataset.target;
  const duration = 1800;
  const start = performance.now();
  function step(now) {
    const p = Math.min((now - start) / duration, 1);
    const ease = 1 - Math.pow(1 - p, 3);
    el.textContent = Math.round(ease * target);
    if (p < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

const countersObserver = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.querySelectorAll('.stat-num').forEach(animateCounter);
      countersObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

const statsSection = document.getElementById('hero-stats');
if (statsSection) countersObserver.observe(statsSection);


// ── Scroll reveal animations ──
const revealEls = document.querySelectorAll(
  '.feature-card, .step-item, .reveal, .reveal-left, .reveal-right, .download-card, .oss-card'
);

const revealObs = new IntersectionObserver(entries => {
  entries.forEach((entry, i) => {
    if (entry.isIntersecting) {
      setTimeout(() => {
        entry.target.classList.add('visible');
      }, entry.target.dataset.delay || 0);
      revealObs.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

// Stagger feature cards
document.querySelectorAll('.feature-card').forEach((card, i) => {
  card.classList.add('reveal');
  card.dataset.delay = i * 100;
});

document.querySelectorAll('.step-item').forEach((step, i) => {
  step.classList.add('reveal');
  step.dataset.delay = i * 150;
});

revealEls.forEach(el => revealObs.observe(el));
document.querySelectorAll('.reveal, .reveal-left, .reveal-right').forEach(el => revealObs.observe(el));


// ── Download button ripple effect ──
document.querySelectorAll('.btn-download, .btn-primary').forEach(btn => {
  btn.addEventListener('click', function (e) {
    const ripple = document.createElement('span');
    const rect = this.getBoundingClientRect();
    ripple.style.cssText = `
      position:absolute; border-radius:50%;
      width:20px; height:20px;
      background:rgba(255,255,255,0.35);
      left:${e.clientX - rect.left - 10}px;
      top:${e.clientY - rect.top - 10}px;
      transform:scale(0);
      animation:ripple-anim 0.55s ease-out forwards;
      pointer-events:none;
    `;
    this.style.position = 'relative';
    this.style.overflow = 'hidden';
    this.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  });
});

// Ripple keyframe injection
const style = document.createElement('style');
style.textContent = `
  @keyframes ripple-anim {
    to { transform: scale(18); opacity: 0; }
  }
`;
document.head.appendChild(style);


// ── Typewriter effect for hero badge ──
(function () {
  const badge = document.getElementById('hero-badge');
  if (!badge) return;
  const textSpan = badge.querySelector('span:last-child');
  const fullText = textSpan.textContent;
  textSpan.textContent = '';
  let i = 0;
  setTimeout(() => {
    const timer = setInterval(() => {
      textSpan.textContent += fullText[i++];
      if (i >= fullText.length) clearInterval(timer);
    }, 45);
  }, 300);
})();


// ── Mock console typing animation ──
(function () {
  const lines = document.querySelectorAll('.console-line');
  lines.forEach((line, i) => {
    line.style.opacity = '0';
    setTimeout(() => {
      line.style.transition = 'opacity 0.4s';
      line.style.opacity = '1';
    }, 1200 + i * 500);
  });
})();


// ── Glowing cursor trail on hero ──
(function () {
  const hero = document.getElementById('hero');
  if (!hero) return;
  let trail = [];

  hero.addEventListener('mousemove', (e) => {
    const dot = document.createElement('div');
    dot.style.cssText = `
      position:fixed; pointer-events:none; z-index:9999;
      width:6px; height:6px; border-radius:50%;
      background:rgba(0,212,255,0.6);
      left:${e.clientX - 3}px; top:${e.clientY - 3}px;
      transition:opacity 0.5s, transform 0.5s;
      box-shadow:0 0 10px rgba(0,212,255,0.8);
    `;
    document.body.appendChild(dot);
    trail.push(dot);
    if (trail.length > 12) {
      const old = trail.shift();
      old.style.opacity = '0';
      old.style.transform = 'scale(0)';
      setTimeout(() => old.remove(), 500);
    }
    requestAnimationFrame(() => {
      dot.style.opacity = '0';
      dot.style.transform = 'scale(0.3)';
    });
    setTimeout(() => dot.remove(), 600);
  });
})();

// -- Registration Modal & Form Logic --
(function () {
  const modal = document.getElementById('registration-modal');
  const btnClose = document.getElementById('close-modal');
  const form = document.getElementById('registration-form');
  const msgBox = document.getElementById('reg-message');

  const triggers = [
    document.getElementById('btn-hero-download'),
    document.getElementById('btn-main-download'),
    document.getElementById('nav-download')
  ];

  function openModal(e) {
    if (e) e.preventDefault();
    modal.classList.add('active');
    msgBox.style.display = 'none';
    form.reset();
  }

  function closeModal() {
    modal.classList.remove('active');
  }

  triggers.forEach(btn => {
    if (btn) btn.addEventListener('click', openModal);
  });

  if (btnClose) btnClose.addEventListener('click', closeModal);

  window.addEventListener('click', (e) => {
    if (e.target === modal) closeModal();
  });

  if (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();

      const submitBtn = document.getElementById('btn-submit-reg');
      const originalText = submitBtn.innerHTML;
      submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Processing...';
      submitBtn.disabled = true;

      const data = {
        name: document.getElementById('reg-name').value,
        phone: document.getElementById('reg-phone').value,
        email: document.getElementById('reg-email').value,
        country: document.getElementById('reg-country').value,
        date: new Date().toISOString()
      };

      // ✅ STEP 1: Trigger download IMMEDIATELY (before any async/await)
      // This must happen synchronously inside the user gesture handler
      const dlLink = document.createElement('a');
      dlLink.href = 'https://github.com/abdllaouidjabere-cmyk/Tweakify/releases/latest/download/Tweakify.exe';
      dlLink.target = '_blank';
      document.body.appendChild(dlLink);
      dlLink.click();
      document.body.removeChild(dlLink);

      // ✅ STEP 2: Show success message
      msgBox.className = 'reg-message success';
      msgBox.innerHTML = '<i class="fa-solid fa-check-circle" style="margin-right:6px;"></i>Registration successful! Downloading...';
      msgBox.style.display = 'block';

      submitBtn.innerHTML = originalText;
      submitBtn.disabled = false;

      // ✅ STEP 3: Save data in background (fire & forget - doesn't block download)
      // Save to localStorage
      try {
        const existing = JSON.parse(localStorage.getItem('tweakify_users') || '[]');
        existing.push(data);
        localStorage.setItem('tweakify_users', JSON.stringify(existing));
      } catch (err) { }

      // Save to server in background (non-blocking)
      fetch('api.php', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
      }).catch(() => { });

      // Close modal after 2.5 seconds
      setTimeout(closeModal, 2500);
    });
  }
})();
