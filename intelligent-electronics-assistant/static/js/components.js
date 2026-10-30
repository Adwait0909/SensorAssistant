// Component Inventory Management Logic (Vanilla JS + Fetch API)

let allComponents = [];

document.addEventListener('DOMContentLoaded', () => {
  loadComponents();

  document.getElementById('component-search').addEventListener('input', debounce(applyFilters, 300));
  document.getElementById('category-filter').addEventListener('change', applyFilters);
  document.getElementById('voltage-filter').addEventListener('change', applyFilters);
});

async function loadComponents() {
  try {
    const res = await fetch('/api/components');
    const data = await res.json();
    if (data.status === 'success') {
      allComponents = data.data;
      renderComponents(allComponents);
    } else {
      showToast('Error loading components: ' + data.message, 'error');
    }
  } catch (err) {
    showToast('Network error while fetching components', 'error');
  }
}

function renderComponents(components) {
  const tbody = document.getElementById('components-tbody');
  tbody.innerHTML = '';

  if (components.length === 0) {
    tbody.innerHTML = `
      <tr>
        <td colspan="8" style="text-align: center; color: var(--text-dim); padding: 30px;">
          No components found matching the selected filter.
        </td>
      </tr>
    `;
    return;
  }

  components.forEach(c => {
    const tr = document.createElement('tr');
    tr.innerHTML = `
      <td>
        <div style="font-weight: 600; color: #fff;">${escapeHtml(c.name)}</div>
        <div style="font-size: 11px; color: var(--text-dim);">${escapeHtml(c.sub_category || '')}</div>
      </td>
      <td><span class="badge badge-info">${escapeHtml(c.category)}</span></td>
      <td>
        <div style="display:flex; align-items:center; gap:6px;">
          <span>${c.quantity}</span>
          <button onclick="quickUpdateQty('${c.id}', ${c.quantity + 1})" style="padding:2px 6px; font-size:10px; cursor:pointer;" class="btn btn-secondary">+</button>
        </div>
      </td>
      <td><code>${escapeHtml(c.voltage || '5V')}</code></td>
      <td>₹${c.cost.toFixed(2)}</td>
      <td><span class="badge badge-success">${escapeHtml(c.availability)}</span></td>
      <td style="max-width: 220px; font-size: 11.5px; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(c.safety_notes || '')}">
        ${escapeHtml(c.safety_notes || 'No known hazards')}
      </td>
      <td style="text-align: right;">
        <div style="display:inline-flex; gap: 6px;">
          <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px;" onclick="editComponent('${c.id}')">Edit</button>
          <button class="btn btn-danger" style="padding: 4px 8px; font-size: 11px;" onclick="deleteComponent('${c.id}')">Delete</button>
        </div>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

function applyFilters() {
  const searchVal = document.getElementById('component-search').value.toLowerCase();
  const catVal = document.getElementById('category-filter').value;
  const voltVal = document.getElementById('voltage-filter').value;

  const filtered = allComponents.filter(c => {
    const matchesSearch = !searchVal || 
      c.name.toLowerCase().includes(searchVal) || 
      (c.description && c.description.toLowerCase().includes(searchVal)) ||
      (c.aliases && c.aliases.some(a => a.toLowerCase().includes(searchVal)));

    const matchesCategory = catVal === 'All' || c.category === catVal;
    const matchesVoltage = voltVal === 'All' || (c.voltage && c.voltage.includes(voltVal));

    return matchesSearch && matchesCategory && matchesVoltage;
  });

  renderComponents(filtered);
}

function openAddComponentModal() {
  document.getElementById('modal-title').innerText = 'Add New Component';
  document.getElementById('comp-id').value = '';
  document.getElementById('comp-name').value = '';
  document.getElementById('comp-category').value = 'Controllers';
  document.getElementById('comp-subcategory').value = '';
  document.getElementById('comp-quantity').value = 1;
  document.getElementById('comp-voltage').value = '5V';
  document.getElementById('comp-cost').value = '0.0';
  document.getElementById('comp-desc').value = '';
  document.getElementById('comp-safety').value = '';

  document.getElementById('component-modal').classList.add('active');
}

function closeComponentModal() {
  document.getElementById('component-modal').classList.remove('active');
}

function editComponent(id) {
  const comp = allComponents.find(c => c.id === id);
  if (!comp) return;

  document.getElementById('modal-title').innerText = 'Edit Component';
  document.getElementById('comp-id').value = comp.id;
  document.getElementById('comp-name').value = comp.name;
  document.getElementById('comp-category').value = comp.category;
  document.getElementById('comp-subcategory').value = comp.sub_category || '';
  document.getElementById('comp-quantity').value = comp.quantity;
  document.getElementById('comp-voltage').value = comp.voltage || '5V';
  document.getElementById('comp-cost').value = comp.cost || 0.0;
  document.getElementById('comp-desc').value = comp.description || '';
  document.getElementById('comp-safety').value = comp.safety_notes || '';

  document.getElementById('component-modal').classList.add('active');
}

async function handleComponentSubmit(e) {
  e.preventDefault();
  const id = document.getElementById('comp-id').value;
  const payload = {
    name: document.getElementById('comp-name').value,
    category: document.getElementById('comp-category').value,
    sub_category: document.getElementById('comp-subcategory').value,
    quantity: parseInt(document.getElementById('comp-quantity').value) || 1,
    voltage: document.getElementById('comp-voltage').value,
    cost: parseFloat(document.getElementById('comp-cost').value) || 0.0,
    description: document.getElementById('comp-desc').value,
    safety_notes: document.getElementById('comp-safety').value
  };

  try {
    let url = '/api/components';
    let method = 'POST';

    if (id) {
      url = `/api/components/${id}`;
      method = 'PUT';
    }

    const res = await fetch(url, {
      method: method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const result = await res.json();
    if (result.status === 'success') {
      showToast(result.message || 'Saved successfully', 'success');
      closeComponentModal();
      loadComponents();
    } else {
      showToast(result.message, 'error');
    }
  } catch (err) {
    showToast('Failed to save component', 'error');
  }
}

async function quickUpdateQty(id, newQty) {
  try {
    const res = await fetch(`/api/components/${id}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quantity: newQty })
    });
    if (res.ok) {
      loadComponents();
    }
  } catch (e) {
    showToast('Failed to update quantity', 'error');
  }
}

async function deleteComponent(id) {
  if (!confirm('Are you sure you want to remove this component from inventory?')) return;

  try {
    const res = await fetch(`/api/components/${id}`, { method: 'DELETE' });
    const result = await res.json();
    if (result.status === 'success') {
      showToast('Component removed', 'info');
      loadComponents();
    } else {
      showToast(result.message, 'error');
    }
  } catch (err) {
    showToast('Error deleting component', 'error');
  }
}

function debounce(fn, delay) {
  let timer;
  return function(...args) {
    clearTimeout(timer);
    timer = setTimeout(() => fn.apply(this, args), delay);
  };
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
