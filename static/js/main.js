// Shri Shivaji Science College - CIMS Client Utilities

document.addEventListener('DOMContentLoaded', () => {
  // Initialize tooltips if Bootstrap is present
  if (window.bootstrap && window.bootstrap.Tooltip) {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));
  }

  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(alert => {
    setTimeout(() => {
      try {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
      } catch (e) {}
    }, 6000);
  });

  // Dynamic Student vs Faculty/Teacher toggle adaptation
  const typeStudent = document.getElementById('typeStudent');
  const typeFaculty = document.getElementById('typeFaculty');
  const nameLabel = document.getElementById('nameLabel');
  const emailLabel = document.getElementById('emailLabel');
  const idLabel = document.getElementById('idLabel');
  const requesterNameInput = document.getElementById('requester_name');
  const requesterEmailInput = document.getElementById('requester_email');
  const requesterIdInput = document.getElementById('requester_id_num');

  function updateRequesterTypeUI() {
    if (!typeStudent || !typeFaculty) return;
    if (typeFaculty.checked) {
      if (nameLabel) nameLabel.innerHTML = `Full Name (Teacher / Faculty) <span class="text-danger">*</span>`;
      if (emailLabel) emailLabel.innerHTML = `Official Faculty Email <span class="text-danger">*</span>`;
      if (idLabel) idLabel.textContent = `Faculty Employee ID / Cabin No`;
      if (requesterNameInput) requesterNameInput.placeholder = `e.g. Prof. Yash Kale / Dr. Deshmukh`;
      if (requesterEmailInput) requesterEmailInput.placeholder = `e.g. faculty.name@shivajisc.org`;
      if (requesterIdInput) requesterIdInput.placeholder = `e.g. FAC-CS-102 or EMP-405`;
    } else {
      if (nameLabel) nameLabel.innerHTML = `Full Name (Student) <span class="text-danger">*</span>`;
      if (emailLabel) emailLabel.innerHTML = `Student Email Address <span class="text-danger">*</span>`;
      if (idLabel) idLabel.textContent = `College Roll No / PRN No`;
      if (requesterNameInput) requesterNameInput.placeholder = `e.g. Athar Khan (Final Year B.Sc)`;
      if (requesterEmailInput) requesterEmailInput.placeholder = `e.g. athar.student@shivajisc.org`;
      if (requesterIdInput) requesterIdInput.placeholder = `e.g. STU-2023-CS-042`;
    }
  }

  if (typeStudent && typeFaculty) {
    typeStudent.addEventListener('change', updateRequesterTypeUI);
    typeFaculty.addEventListener('change', updateRequesterTypeUI);
    updateRequesterTypeUI();
  }

  // Dynamic Item selector stock preview in Request Form
  const itemSelect = document.getElementById('itemSelect');
  const availableBadge = document.getElementById('availableStockBadge');
  const maxQtyHint = document.getElementById('maxQtyHint');
  const qtyInput = document.getElementById('requestedQuantity');

  if (itemSelect && availableBadge) {
    function updateStockBadge() {
      const selected = itemSelect.options[itemSelect.selectedIndex];
      if (selected && selected.value) {
        const stock = parseInt(selected.getAttribute('data-stock') || '0', 10);
        const unit = selected.getAttribute('data-unit') || 'Units';
        availableBadge.innerHTML = `<span class="badge ${stock > 0 ? 'bg-success' : 'bg-danger'} px-3 py-2 fs-6">
          <i class="bi bi-box-seam me-1"></i> Available Now: ${stock} ${unit}
        </span>`;
        if (maxQtyHint) {
          maxQtyHint.textContent = `Physical in store: ${stock} ${unit}. Requests exceeding balance will require administrative replenishment.`;
        }
        if (qtyInput) {
          qtyInput.max = stock > 0 ? stock * 2 : 100; // allow request but advise
        }
      } else {
        availableBadge.innerHTML = `<span class="badge bg-secondary px-3 py-2">Select an item above to view available stock</span>`;
      }
    }

    itemSelect.addEventListener('change', updateStockBadge);
    // Trigger on initial load if preselected
    if (itemSelect.value) {
      updateStockBadge();
    }
  }

  // Copy tracking code to clipboard helper
  const copyButtons = document.querySelectorAll('.btn-copy-code');
  copyButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const code = btn.getAttribute('data-code');
      if (code) {
        navigator.clipboard.writeText(code).then(() => {
          const original = btn.innerHTML;
          btn.innerHTML = `<i class="bi bi-check-lg text-success me-1"></i> Copied!`;
          setTimeout(() => {
            btn.innerHTML = original;
          }, 2000);
        });
      }
    });
  });
});

// Decline Request modal helper
function openDeclineModal(reqId, trackingCode) {
  const form = document.getElementById('declineForm');
  const modalCode = document.getElementById('declineModalTrackingCode');
  if (form) {
    form.action = `/requests/${reqId}/decline`;
  }
  if (modalCode) {
    modalCode.textContent = trackingCode;
  }
  const modal = new bootstrap.Modal(document.getElementById('declineModal'));
  modal.show();
}

// Replenish stock modal helper
function openReplenishModal(itemId, itemName, currentStock, unit) {
  const form = document.getElementById('replenishForm');
  const nameEl = document.getElementById('replenishItemName');
  const stockEl = document.getElementById('replenishCurrentStock');
  if (form) {
    form.action = `/inventory/${itemId}/replenish`;
  }
  if (nameEl) nameEl.textContent = itemName;
  if (stockEl) stockEl.textContent = `${currentStock} ${unit}`;
  const modal = new bootstrap.Modal(document.getElementById('replenishModal'));
  modal.show();
}

// Edit item modal helper
function openEditItemModal(itemId, itemName, minQty, location, desc) {
  const form = document.getElementById('editItemForm');
  if (form) {
    form.action = `/inventory/${itemId}/edit`;
    document.getElementById('editItemName').value = itemName || '';
    document.getElementById('editItemMinQty').value = minQty || 5;
    document.getElementById('editItemLocation').value = location || '';
    document.getElementById('editItemDesc').value = desc || '';
  }
  const modal = new bootstrap.Modal(document.getElementById('editItemModal'));
  modal.show();
}
