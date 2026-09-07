document.addEventListener("DOMContentLoaded", () => {
    const balanceEl = document.getElementById("wallet-balance");
    if (!balanceEl) return;

    // Poll for balance changes (e.g. if another tab / user sent you money)
    setInterval(async () => {
        try {
            const res = await fetch("/api/balance");
            if (!res.ok) return;
            const data = await res.json();
            const formatted = "₦" + data.balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            if (balanceEl.textContent.trim() !== formatted) {
                balanceEl.textContent = formatted;
            }
        } catch (err) {
            console.error("Balance polling error", err);
        }
    }, 5000);
});
