// Хранилище выбранных товаров
const cart = [];

// Форматирование цены
function formatPrice(value) {
    return value.toLocaleString('ru-RU') + ' ₽';
}

// Отрисовка корзины
function renderCart() {
    const list = document.getElementById('cart-list');
    const totalEl = document.getElementById('cart-total');
    const emptyEl = document.getElementById('cart-empty');

    list.innerHTML = '';

    if (cart.length === 0) {
        emptyEl.style.display = 'block';
        totalEl.textContent = '';
        return;
    }

    emptyEl.style.display = 'none';

    let total = 0;

    cart.forEach((item, index) => {
        const li = document.createElement('li');
        const sum = item.price * item.qty;
        total += sum;

        li.innerHTML = `
            <span>${item.name} × ${item.qty} = ${formatPrice(sum)}</span>
            <button data-index="${index}">Удалить</button>
        `;

        list.appendChild(li);
    });

    totalEl.textContent = 'Итого: ' + formatPrice(total);

    // Кнопки удаления
    list.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
            cart.splice(Number(btn.dataset.index), 1);
            renderCart();
        });
    });
}

// Обработка кнопок «Добавить в заявку»
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

    const status = document.getElementById('form-status');

    if (cart.length === 0) {
        status.textContent = 'Сначала добавьте оборудование в заявку.';
        status.style.color = '#ef4444';
        return;
    }

    const formData = new FormData(e.target);

    const payload = {
        name: formData.get('name'),
        phone: formData.get('phone'),
        date_from: formData.get('date_from'),
        date_to: formData.get('date_to'),
        comment: formData.get('comment'),
        items: cart.map(item => ({
            name: item.name,
            qty: item.qty,
            price: item.price,
            sum: item.price * item.qty
        })),
        total: cart.reduce((acc, item) => acc + item.price * item.qty, 0)
    };

    status.textContent = 'Отправляем...';
    status.style.color = '#475569';

    try {
        const response = await fetch('/api/order', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            throw new Error('Сервер вернул ошибку');
        }

        status.textContent = 'Заявка отправлена! Владелец свяжется с вами.';
        status.style.color = '#16a34a';

        // Очищаем корзину и форму
        cart.length = 0;
        renderCart();
        e.target.reset();
    } catch (err) {
        status.textContent = 'Не удалось отправить. Попробуйте позже.';
        status.style.color = '#ef4444';
    }
});

// Первый рендер
renderCart();
// Анимация появления при прокрутке
document.addEventListener('DOMContentLoaded', () => {
    const reveals = document.querySelectorAll('.reveal');

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
            }
        });
    }, { threshold: 0.1 });

    reveals.forEach(reveal => {
        observer.observe(reveal);
    });
});