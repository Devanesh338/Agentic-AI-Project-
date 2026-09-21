const urlParams = new URLSearchParams(window.location.search);
const sessionId = urlParams.get('session_id');
const threadId = urlParams.get('thread_id');

const loader = document.getElementById('loader');
const bookingView = document.getElementById('booking-view');
const successView = document.getElementById('success-view');
const errorView = document.getElementById('error-view');
const itineraryItems = document.getElementById('itinerary-items');
const totalAmountEl = document.getElementById('total-amount');
const btnApprove = document.getElementById('btn-approve');
const ticketsContainer = document.getElementById('tickets-container');
const btnReturn = document.getElementById('btn-return');
const errorMessage = document.getElementById('error-message');

let currentSession = null;

async function fetchSession() {
    if (!sessionId || !threadId) {
        showError("Invalid link. Missing session or thread parameters.");
        return;
    }

    try {
        const response = await fetch(`/api/sessions/${sessionId}`);
        if (!response.ok) {
            let errorMsg = await response.text();
            try {
                const errData = JSON.parse(errorMsg);
                if (errData && errData.message) {
                    errorMsg = `${errData.message} (${response.status}): ${errData.session_id || sessionId}`;
                }
            } catch (e) {}
            throw new Error(errorMsg);
        }
        const data = await response.json();
        currentSession = data;
        renderBooking();
    } catch (err) {
        showError(err.message || "Could not load your booking. It might have expired or doesn't exist.");
    }
}

function renderBooking() {
    loader.classList.add('hidden');
    bookingView.classList.remove('hidden');

    let html = '';
    currentSession.booking_items.forEach(item => {
        let title = item.type;
        let subtitle = item.provider;
        
        if (item.type === 'flight') {
            title = `✈️ Flight to ${item.details.to || item.details.destination || 'Destination'}`;
        } else if (item.type === 'hotel') {
            title = `🏨 Hotel: ${item.details.hotel_name || item.details.name || 'Stay'}`;
        } else if (item.type === 'train') {
            title = `🚆 Train: ${item.details.train_name || item.details.to || item.details.destination || 'Destination'}`;
        } else if (item.type === 'bus') {
            title = `🚌 Bus to ${item.details.to || item.details.destination || 'Destination'}`;
        }

        html += `
            <div class="item-row">
                <div class="item-info">
                    <h4>${title}</h4>
                    <p>${subtitle}</p>
                </div>
                <div class="item-price">
                    ₹${item.price.toLocaleString()}
                </div>
            </div>
        `;
    });

    itineraryItems.innerHTML = html;
    totalAmountEl.textContent = `₹${currentSession.total_amount.toLocaleString()}`;
}

async function approvePayment() {
    btnApprove.classList.add('loading');
    btnApprove.disabled = true;
    btnApprove.querySelector('span').textContent = "Processing...";

    try {
        const payload = {
            session_id: sessionId,
            thread_id: threadId,
            amount: currentSession.total_amount,
            currency: currentSession.currency
        };

        const response = await fetch('/api/payment/approve', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            let errorMsg = await response.text();
            try {
                const errData = JSON.parse(errorMsg);
                if (errData && errData.message) {
                    errorMsg = `${errData.message} (${response.status})`;
                }
            } catch (e) {}
            throw new Error(errorMsg);
        }

        const result = await response.json();
        if (result.success && result.tickets) {
            renderTickets(result.tickets);
        } else {
            throw new Error("Failed to retrieve tickets.");
        }
    } catch (err) {
        btnApprove.classList.remove('loading');
        btnApprove.disabled = false;
        btnApprove.querySelector('span').textContent = "Approve Payment & Book";
        alert("Payment failed: " + err.message);
    }
}

function renderTickets(tickets) {
    bookingView.classList.add('hidden');
    successView.classList.remove('hidden');

    let html = '';
    tickets.forEach((ticket, i) => {
        let detailsHtml = '';
        const data = ticket.details || {};
        
        if (ticket.type === 'flight' || ticket.type === 'train' || ticket.type === 'bus') {
            const fromLoc = data.from || data.origin;
            const toLoc = data.to || data.destination;
            
            if (!fromLoc) {
                console.error(`Missing route information (from) for booking item: ${ticket.reference}`);
            }
            if (!toLoc) {
                console.error(`Missing route information (to) for booking item: ${ticket.reference}`);
            }
        }
        
        if (ticket.type === 'flight') {
            detailsHtml = `
                <div class="ticket-detail"><span>Departure</span><strong>${(data.departure || '').replace('T', ' ')}</strong></div>
                <div class="ticket-detail"><span>From</span><strong>${data.from || data.origin || 'N/A'}</strong></div>
                <div class="ticket-detail"><span>To</span><strong>${data.to || data.destination || 'N/A'}</strong></div>
                <div class="ticket-detail"><span>Airline</span><strong>${data.provider || 'N/A'}</strong></div>
            `;
        } else if (ticket.type === 'train') {
            detailsHtml = `
                <div class="ticket-detail"><span>Departure</span><strong>${(data.departure || 'Pending').replace('T', ' ')}</strong></div>
                <div class="ticket-detail"><span>From</span><strong>${data.from || data.origin || 'Origin'}</strong></div>
                <div class="ticket-detail"><span>To</span><strong>${data.to || data.destination || 'Destination'}</strong></div>
                <div class="ticket-detail"><span>Train</span><strong>${data.train_name || data.name || 'N/A'} (${data.class || data.train_number || ''})</strong></div>
            `;
        } else if (ticket.type === 'bus') {
            detailsHtml = `
                <div class="ticket-detail"><span>Departure</span><strong>${(data.departure || 'Pending').replace('T', ' ')}</strong></div>
                <div class="ticket-detail"><span>From</span><strong>${data.from || data.origin || 'Origin'}</strong></div>
                <div class="ticket-detail"><span>To</span><strong>${data.to || data.destination || 'Destination'}</strong></div>
                <div class="ticket-detail"><span>Bus</span><strong>${data.bus_name || data.name || 'N/A'}</strong></div>
            `;
        } else if (ticket.type === 'hotel') {
            detailsHtml = `
                <div class="ticket-detail"><span>Hotel</span><strong>${data.hotel_name || data.name || 'N/A'}</strong></div>
                <div class="ticket-detail"><span>Room</span><strong>${data.room_type || 'Standard'}</strong></div>
                <div class="ticket-detail"><span>Location</span><strong>${data.location || 'Confirmed'}</strong></div>
            `;
        }

        html += `
            <div class="ticket-card" style="animation-delay: ${i * 0.1}s">
                <div class="ticket-header">
                    <span class="type">${ticket.type}</span>
                    <span class="pnr">${ticket.reference}</span>
                </div>
                <div class="ticket-body">
                    ${detailsHtml}
                </div>
            </div>
        `;
    });

    ticketsContainer.innerHTML = html;
}

function showError(msg) {
    loader.classList.add('hidden');
    errorView.classList.remove('hidden');
    errorMessage.textContent = msg;
}

btnApprove.addEventListener('click', approvePayment);
btnReturn.addEventListener('click', () => {
    window.location.href = 'http://localhost:8501/';
});

// Init
fetchSession();
