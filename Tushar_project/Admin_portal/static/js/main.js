// Utility Functions

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-IN', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusColor(status) {
    const colors = {
        'processing': 'processing',
        'shipped': 'shipped',
        'delivered': 'delivered',
        'cancelled': 'cancelled',
        'pending': 'pending',
        'completed': 'delivered'
    };
    return colors[status] || 'processing';
}

function getPaymentColor(status) {
    const colors = {
        'pending': 'pending',
        'paid': 'paid',
        'failed': 'failed',
        'refunded': 'refunded'
    };
    return colors[status] || 'pending';
}

// Toast Notifications
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function showSuccess(message) {
    showToast(message, 'success');
}

function showError(message) {
    showToast(message, 'error');
}

// Handle fetch errors
async function handleResponse(response) {
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'An error occurred');
    }
    return response.json();
}
