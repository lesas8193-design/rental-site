const cart = [];
const totalEl = document.getElementById('cart-total');
const formStatus = document.getElementById('form-status');

// Форматирование
function formatPrice(value) {
    return value.toLocaleString('ru-RU') + ' ₽';
}

// Подсчет дней для предварительного просмотра
function getDaysCount() {
    const dateFrom = document.querySelector('input[name="date_from"]').value;
    const dateTo = document.querySelector('input[name="date_to"]').value;
    if (!dateFrom || !dateTo) return 1;
    
    const d1 = new Date(dateFrom);
    const d2 = new Date(dateTo);
    const diffTime = Math.abs(d2 - d1);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24)) + 1; // +1, чтобы включить оба дня
    return isNaN(diffDays) || diffDays < 1 ? 1 : diffDays;
}

function renderCart() {
    const list = document.getElementById('cart-list');
    const emptyEl = document.getElementById('cart-empty');

    list.innerHTML = '';
    
    if (cart.length === 0) {
        emptyEl.style.display = 'block';
        totalEl.textContent = '';
        return;
    }

    emptyEl.style.display = 'none';
    let total = 0;
    const days = getDaysCount();

    cart.forEach((item, index) => {
        const li = document.createElement('li');
        const sum = item.price * item.qty * days; // Умножаем на дни
        total += sum;

        li.innerHTML = `
            <span>${item.name} × ${item.qty} = ${formatPrice(sum)}</span>
            <button data-index="${index}">Удалить</button>
        `;
        list.appendChild(li);
    });

    totalEl.innerHTML = `Итого за ${days} дн.: <br>${formatPrice(total)}`;

    // Удаление
    list.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            cart.splice(Number(btn.dataset.index), 1);
            renderCart();
        });
    });
}

// Пересчитываем корзину, если изменились даты
document.querySelectorAll('input[type="date"]').forEach(input => {
    input.addEventListener('change', renderCart);
});

// Добавление в корзину
document.querySelectorAll('.add-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const card = btn.closest('.card');
        const id = card.dataset.id;
        const name = card.dataset.name;
        const price = Number(card.dataset.price);

        const existing = cart.find(item => item.id === id);
        if (existing) {
            existing.qty += 1;
        } else {
            cart.push({ id, name, price, qty: 1 });
        }
        renderCart();
    });
});

// Отправка формы
document.getElementById('order-form').addEventListener('submit', async (e) => {
    e.preventDefault();

    if (cart.length === 0) {
        formStatus.textContent = 'Сначала добавьте оборудование в заявку.';
        formStatus.style.color = '#ef4444';
        return;
    }

    const formData = new FormData(e.target);
    
    // Передаем на сервер только id и количество, цены пусть считает сервер!
    const payload = {
        name: formData.get('name'),
        phone: formData.get('phone'),
        date_from: formData.get('date_from'),
        date_to: formData.get('date_to'),
        comment: formData.get('comment'),
        items: cart.map(item => ({ id: item.id, qty: item.qty }))
    };

    formStatus.textContent = 'Отправляем...';
    formStatus.style.color = '#475569';

    try {
        const response = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const result = await response.json();

        if (!response.ok || !result.ok) {
            throw new Error(result.error || 'Ошибка сервера');
        }

        formStatus.textContent = 'Заявка отправлена! Владелец свяжется с вами.';
        formStatus.style.color = '#16a34a';
        cart.length = 0;
        renderCart();
        e.target.reset();
    } catch (err) {
        formStatus.textContent = err.message;
        formStatus.style.color = '#ef4444';
    }
});

// Анимация появления
document.addEventListener('DOMContentLoaded', () => {
    const reveals = document.querySelectorAll('.reveal');
    if (!window.IntersectionObserver) {
        reveals.forEach(r => r.classList.add('active'));
        return;
    }
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) entry.target.classList.add('active');
        });
    }, { threshold: 0.1 });
    reveals.forEach(reveal => observer.observe(reveal));
});