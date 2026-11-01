/**
 * BookEase Web Portal — Booking Wizard JavaScript
 * Handles: multi-step wizard, service/staff selection, slot loading, form validation, booking submission.
 */

'use strict';

/* ── State ────────────────────────────────────────────────────────────────── */
const state = {
  serviceId:   parseInt(document.getElementById('selectedServiceId')?.value) || null,
  staffId:     parseInt(document.getElementById('selectedStaffId')?.value)   || null,
  serviceName: '',
  staffName:   '',
  price:       0,
  duration:    0,
  optionId:    null,
  options:     [],
  date:        '',
  startTime:   '',
  currentStep: 1,
};

const currency = document.getElementById('currencySymbol')?.value || '$';
const todayStr = document.getElementById('todayDate')?.value || new Date().toISOString().split('T')[0];


/* ── Utilities ────────────────────────────────────────────────────────────── */
function fmt(date) {
  if (!date) return '—';
  try {
    const d = new Date(date + 'T00:00:00');
    return d.toLocaleDateString(undefined, { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' });
  } catch { return date; }
}

function fmtTime(t) {
  if (!t) return '—';
  try {
    const [h, m] = t.split(':').map(Number);
    const ampm = h >= 12 ? 'PM' : 'AM';
    const hr = h % 12 || 12;
    return `${hr}:${m.toString().padStart(2, '0')} ${ampm}`;
  } catch { return t; }
}

function setEl(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text;
}

function setHidden(id, value) {
  const el = document.getElementById(id);
  if (el) el.value = value;
}


/* ── Step Navigation ──────────────────────────────────────────────────────── */
function goToStep(step) {
  // Validate forward navigation
  if (step > state.currentStep) {
    if (step === 2 && (!state.serviceId || !state.staffId)) {
      showToast('Please select a service and specialist first.', 'error');
      return;
    }
    if (step === 3 && (!state.date || !state.startTime)) {
      showToast('Please select a date and time slot.', 'error');
      return;
    }
  }

  document.querySelectorAll('.wizard-step').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.progress-step').forEach((el, i) => {
    el.classList.remove('active', 'done');
    if (i + 1 < step)      el.classList.add('done');
    else if (i + 1 === step) el.classList.add('active');
  });

  const target = document.getElementById(`step-${step}`);
  if (target) {
    target.classList.add('active');
    // Smooth scroll to top of wizard on step change
    target.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  state.currentStep = step;

  // Populate summary bar on step 2
  if (step === 2) {
    setEl('sum-service-name', state.serviceName);
    setEl('sum-staff-name',   state.staffName);
  }

  // Populate review card on step 3
  if (step === 3) {
    setEl('rev-service', state.serviceName);
    setEl('rev-duration', state.duration ? `${state.duration} min` : '—');
    setEl('rev-staff',   state.staffName);
    setEl('rev-date',    fmt(state.date));
    setEl('rev-time',    fmtTime(state.startTime));
    setEl('rev-price',   `${currency}${parseFloat(state.price || 0).toFixed(0)}`);
  }
}
window.goToStep = goToStep;


/* ── Service Selection ───────────────────────────────────────────────────── */
function initServiceCards() {
  const cards = document.querySelectorAll('.service-select-card');
  cards.forEach(card => {
    card.addEventListener('click', () => {
      cards.forEach(c => {
        c.classList.remove('selected');
        c.setAttribute('aria-pressed', 'false');
      });
      card.classList.add('selected');
      card.setAttribute('aria-pressed', 'true');

      state.serviceId   = parseInt(card.dataset.serviceId);
      state.serviceName = card.dataset.serviceName;
      state.price       = parseFloat(card.dataset.servicePrice) || 0;
      state.duration    = parseInt(card.dataset.serviceDuration) || 60;

      // Parse duration options (if any)
      state.options = [];
      state.optionId = null;
      try {
        state.options = JSON.parse(card.dataset.options || '[]');
      } catch { state.options = []; }

      // Reset downstream state
      state.staffId   = null;
      state.staffName = '';
      state.date      = '';
      state.startTime = '';
      setHidden('selectedServiceId', state.serviceId);
      setHidden('selectedStaffId',   '');

      // Show duration selector if the service offers options
      if (state.options.length > 0) {
        renderDurationOptions(state.options);
      } else {
        hideDurationSection();
      }

      // Load staff for this service
      loadStaff(state.serviceId);

      checkStep1Complete();
    });
  });
}


/* ── Duration Options ─────────────────────────────────────────────────────── */
function renderDurationOptions(options) {
  const section = document.getElementById('durationSection');
  const grid    = document.getElementById('durationGrid');
  if (!section || !grid) return;

  grid.innerHTML = options.map((opt, i) => `
    <button class="duration-select-card${i === 0 ? ' selected' : ''}"
            data-option-id="${opt.id}"
            data-duration="${opt.duration_minutes}"
            data-price="${opt.price}"
            data-label="${escHtml(opt.label)}"
            type="button"
            aria-pressed="${i === 0 ? 'true' : 'false'}">
      <span class="dsc-label">${escHtml(opt.label)}</span>
      <span class="dsc-price">${currency}${parseFloat(opt.price).toFixed(0)}</span>
    </button>`).join('');

  section.style.display = 'block';

  // Auto-select the first option
  selectDuration(options[0]);

  grid.querySelectorAll('.duration-select-card').forEach(card => {
    card.addEventListener('click', () => {
      grid.querySelectorAll('.duration-select-card').forEach(c => {
        c.classList.remove('selected');
        c.setAttribute('aria-pressed', 'false');
      });
      card.classList.add('selected');
      card.setAttribute('aria-pressed', 'true');
      selectDuration({
        id: parseInt(card.dataset.optionId),
        duration_minutes: parseInt(card.dataset.duration),
        price: parseFloat(card.dataset.price),
        label: card.dataset.label,
      });
    });
  });
}

function selectDuration(opt) {
  if (!opt) return;
  state.optionId = opt.id;
  state.duration = opt.duration_minutes;
  state.price    = opt.price;
}

function hideDurationSection() {
  const section = document.getElementById('durationSection');
  if (section) section.style.display = 'none';
}


/* ── Staff Loading ────────────────────────────────────────────────────────── */
async function loadStaff(serviceId) {
  const staffSection = document.getElementById('staffSection');
  const staffGrid    = document.getElementById('staffGrid');
  if (!staffSection || !staffGrid) return;

  staffGrid.innerHTML = '<div class="slots-placeholder"><p>Loading specialists…</p></div>';
  staffSection.style.display = 'block';
  staffSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

  try {
    const res  = await fetch(`/api/staff?service_id=${serviceId}`);
    const data = await res.json();
    const list = data.staff || [];

    if (!list.length) {
      staffGrid.innerHTML = '<div class="empty-state"><p>No specialists available for this service.</p></div>';
      return;
    }

    staffGrid.innerHTML = list.map(st => {
      const initials = st.name.split(' ').map(w => w[0]).join('').substring(0, 2).toUpperCase();
      const isPreselected = state.staffId && state.staffId === st.id;
      return `
        <button class="staff-select-card${isPreselected ? ' selected' : ''}"
                data-staff-id="${st.id}"
                data-staff-name="${escHtml(st.name)}"
                data-staff-role="${escHtml(st.role_title || 'Specialist')}"
                type="button"
                aria-pressed="${isPreselected ? 'true' : 'false'}">
          <div class="ssa-avatar" style="background:${escHtml(st.color_code || '#C4627A')}20;color:${escHtml(st.color_code || '#C4627A')}">
            ${escHtml(initials)}
          </div>
          <div>
            <p class="ssa-name">${escHtml(st.name)}</p>
            <p class="ssa-role">${escHtml(st.role_title || 'Specialist')}</p>
          </div>
        </button>`;
    }).join('');

    // Attach events
    staffGrid.querySelectorAll('.staff-select-card').forEach(card => {
      card.addEventListener('click', () => {
        staffGrid.querySelectorAll('.staff-select-card').forEach(c => {
          c.classList.remove('selected');
          c.setAttribute('aria-pressed', 'false');
        });
        card.classList.add('selected');
        card.setAttribute('aria-pressed', 'true');

        state.staffId   = parseInt(card.dataset.staffId);
        state.staffName = card.dataset.staffName;
        setHidden('selectedStaffId', state.staffId);
        checkStep1Complete();
      });
    });

    // If preselected staff, confirm selection
    if (state.staffId) {
      const existing = staffGrid.querySelector(`.staff-select-card[data-staff-id="${state.staffId}"]`);
      if (existing) {
        state.staffName = existing.dataset.staffName;
        checkStep1Complete();
      }
    }

  } catch (err) {
    console.error('Failed to load staff:', err);
    staffGrid.innerHTML = '<div class="empty-state"><p>Could not load specialists. Please refresh.</p></div>';
  }
}


/* ── Step 1 Completion Check ─────────────────────────────────────────────── */
function checkStep1Complete() {
  const btn = document.getElementById('step1Next');
  if (btn) btn.disabled = !(state.serviceId && state.staffId);
}


/* ── Date Picker & Slot Loading ──────────────────────────────────────────── */
function initDatePicker() {
  const datePicker = document.getElementById('datePicker');
  if (!datePicker) return;

  datePicker.addEventListener('change', async () => {
    const selectedDate = datePicker.value;
    if (!selectedDate) return;
    state.date      = selectedDate;
    state.startTime = '';
    setHidden('selectedDate', selectedDate);
    setHidden('selectedStartTime', '');
    document.getElementById('step2Next').disabled = true;

    await loadSlots(selectedDate);
  });
}

async function loadSlots(date) {
  const slotsGrid = document.getElementById('slotsGrid');
  if (!slotsGrid) return;

  if (!state.staffId || !state.serviceId) {
    slotsGrid.innerHTML = '<div class="slots-placeholder"><p>Please select a service and specialist first.</p></div>';
    return;
  }

  slotsGrid.innerHTML = '<div class="slots-placeholder"><span class="slot-loading">⟳ Loading available times…</span></div>';

  try {
    const url = `/api/slots?staff_id=${state.staffId}&service_id=${state.serviceId}&date=${date}${state.duration ? '&duration=' + state.duration : ''}`;
    const res  = await fetch(url);
    const data = await res.json();
    const slots = data.slots || [];

    if (!slots.length) {
      slotsGrid.innerHTML = `<div class="slots-placeholder"><p>No available time slots on this date. Please try another day.</p></div>`;
      return;
    }

    slotsGrid.innerHTML = slots.map(slot => {
      const start = typeof slot === 'string' ? slot : slot.start;
      const end   = typeof slot === 'string' ? null : slot.end;
      const label = end ? `${fmtTime(start)} – ${fmtTime(end)}` : fmtTime(start);
      return `
      <button class="slot-btn" data-time="${escHtml(start)}" type="button" aria-label="Select ${label}">
        ${label}
      </button>`;
    }).join('');

    slotsGrid.querySelectorAll('.slot-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        slotsGrid.querySelectorAll('.slot-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        state.startTime = btn.dataset.time;
        setHidden('selectedStartTime', state.startTime);
        document.getElementById('step2Next').disabled = false;
      });
    });

  } catch (err) {
    console.error('Failed to load slots:', err);
    slotsGrid.innerHTML = '<div class="slots-placeholder"><p>Could not load time slots. Please refresh.</p></div>';
  }
}


/* ── Form Validation ──────────────────────────────────────────────────────── */
function showFieldError(id, msg) {
  const el = document.getElementById(id);
  if (!el) return;
  el.textContent = msg;
  el.style.display = msg ? 'block' : 'none';
}

function clearErrors() {
  ['custName-error', 'custPhone-error', 'custEmail-error'].forEach(id => showFieldError(id, ''));
  const errBanner = document.getElementById('bookingError');
  if (errBanner) errBanner.style.display = 'none';
}

function validateForm() {
  let valid = true;
  clearErrors();

  const name  = document.getElementById('custName')?.value?.trim()  || '';
  const phone = document.getElementById('custPhone')?.value?.trim() || '';
  const email = document.getElementById('custEmail')?.value?.trim() || '';

  if (name.length < 2) {
    showFieldError('custName-error', 'Please enter your full name (at least 2 characters).');
    valid = false;
  }

  if (phone.length < 7) {
    showFieldError('custPhone-error', 'Please enter a valid phone number.');
    valid = false;
  }

  if (email && !/^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$/.test(email)) {
    showFieldError('custEmail-error', 'Please enter a valid email address.');
    valid = false;
  }

  return valid;
}


/* ── Booking Submission ───────────────────────────────────────────────────── */
async function submitBooking() {
  if (!validateForm()) return;

  const name  = document.getElementById('custName')?.value?.trim()  || '';
  const phone = document.getElementById('custPhone')?.value?.trim() || '';
  const email = document.getElementById('custEmail')?.value?.trim() || '';
  const notes = document.getElementById('custNotes')?.value?.trim() || '';

  if (!state.serviceId || !state.staffId || !state.date || !state.startTime) {
    showBookingError('Booking data is incomplete. Please go back and complete all steps.');
    return;
  }

  const confirmBtn = document.getElementById('confirmBtn');
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = '⟳ Confirming…';
  }
  showLoading();

  try {
    const res = await fetch('/api/book', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        service_id:      state.serviceId,
        staff_id:        state.staffId,
        option_id:       state.optionId || undefined,
        date:            state.date,
        start_time:      state.startTime,
        customer_name:   name,
        customer_phone:  phone,
        customer_email:  email || undefined,
        notes:           notes || undefined,
      }),
    });
    const data = await res.json();
    hideLoading();

    if (data.success) {
      showToast('Booking confirmed! Redirecting…', 'success', 2000);
      setTimeout(() => {
        window.location.href = data.redirect || '/';
      }, 1200);
    } else {
      showBookingError(data.error || 'Booking failed. Please try again.');
      if (confirmBtn) {
        confirmBtn.disabled = false;
        confirmBtn.textContent = '✓ Confirm Booking';
      }
    }
  } catch (err) {
    hideLoading();
    console.error('Booking error:', err);
    showBookingError('Network error. Please check your connection and try again.');
    if (confirmBtn) {
      confirmBtn.disabled = false;
      confirmBtn.textContent = '✓ Confirm Booking';
    }
  }
}
window.submitBooking = submitBooking;

function showBookingError(msg) {
  const banner = document.getElementById('bookingError');
  const msgEl  = document.getElementById('bookingErrorMsg');
  if (banner && msgEl) {
    msgEl.textContent = msg;
    banner.style.display = 'block';
    banner.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}


/* ── HTML Escape Utility ─────────────────────────────────────────────────── */
function escHtml(str) {
  return String(str || '').replace(/[&<>"']/g, m => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[m]));
}


/* ── Initialize on DOM Ready ─────────────────────────────────────────────── */
document.addEventListener('DOMContentLoaded', () => {
  initServiceCards();
  initDatePicker();

  // If a service is preselected from URL, auto-load staff
  if (state.serviceId) {
    // Find and highlight the preselected service card
    const preCard = document.querySelector(`.service-select-card[data-service-id="${state.serviceId}"]`);
    if (preCard) {
      state.serviceName = preCard.dataset.serviceName || '';
      state.price       = parseFloat(preCard.dataset.servicePrice) || 0;
      state.duration    = parseInt(preCard.dataset.serviceDuration) || 60;
      try {
        state.options = JSON.parse(preCard.dataset.options || '[]');
      } catch { state.options = []; }
      preCard.classList.add('selected');
      preCard.setAttribute('aria-pressed', 'true');
      if (state.options.length > 0) {
        renderDurationOptions(state.options);
      } else {
        hideDurationSection();
      }
    }
    loadStaff(state.serviceId).then(() => {
      checkStep1Complete();
    });
  }

  // If staff is preselected from URL
  if (state.staffId) {
    checkStep1Complete();
  }

  // Set date picker min/max
  const dp = document.getElementById('datePicker');
  if (dp) {
    dp.min = todayStr;
    const maxDate = new Date(todayStr);
    maxDate.setDate(maxDate.getDate() + 90);
    dp.max = maxDate.toISOString().split('T')[0];
  }
});

