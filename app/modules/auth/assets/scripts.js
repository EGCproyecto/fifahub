document.addEventListener("DOMContentLoaded", () => {
    const challengePage = document.querySelector("[data-two-factor-page]");
    if (!challengePage) {
        return;
    }

    const totpSection = document.getElementById("twoFactorTotpSection");
    const recoverySection = document.getElementById("twoFactorRecoverySection");
    const toggleRecoveryBtn = challengePage.querySelector("[data-toggle-recovery]");
    const toggleTotpBtn = challengePage.querySelector("[data-toggle-totp]");
    const totpForm = document.getElementById("twoFactorTotpForm");
    const recoveryForm = document.getElementById("recoveryCodeForm");

    const toggleSection = (showRecovery) => {
        if (!totpSection || !recoverySection) return;
        if (showRecovery) {
            totpSection.classList.add("d-none");
            recoverySection.classList.remove("d-none");
            const recoveryInput = recoverySection.querySelector("input");
            if (recoveryInput) {
                recoveryInput.focus();
            }
        } else {
            recoverySection.classList.add("d-none");
            totpSection.classList.remove("d-none");
            const totpInput = totpSection.querySelector("input");
            if (totpInput) {
                totpInput.focus();
            }
        }
    };

    const setButtonLoading = (button, loading) => {
        if (!button) return;
        if (loading) {
            if (!button.dataset.originalContent) {
                button.dataset.originalContent = button.innerHTML;
            }
            const text = button.dataset.loadingText || "Verifying...";
            button.innerHTML = `<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>${text}`;
            button.disabled = true;
        } else if (button.dataset.originalContent) {
            button.innerHTML = button.dataset.originalContent;
            button.disabled = false;
        }
    };

    const showFieldError = (target, message) => {
        if (!target) return;
        target.textContent = message || "";
        target.classList.toggle("d-none", !message);
    };

    const handleFormSubmit = (form, mode) => {
        if (!form) return;
        form.addEventListener("submit", async (event) => {
            if (typeof window.fetch !== "function") {
                return;
            }
            event.preventDefault();
            const tokenField = form.querySelector("input[name='token']");
            const valueField =
                mode === "recovery" ? form.querySelector("input[name='recovery_code']") : form.querySelector("input[name='code']");
            const errorTarget = form.querySelector(
                mode === "recovery" ? "[data-error-target='recovery']" : "[data-error-target='totp']",
            );
            const submitButton = form.querySelector("button[type='submit']");
            const payload = { token: (tokenField && tokenField.value) || "" };
            const fieldValue = ((valueField && valueField.value) || "").trim();

            showFieldError(errorTarget, "");

            if (!payload.token) {
                showFieldError(errorTarget, "Two-factor session expired. Please login again.");
                return;
            }

            if (!fieldValue) {
                showFieldError(errorTarget, mode === "recovery" ? "Enter a recovery code." : "Enter your 6-digit code.");
                return;
            }

            if (mode === "recovery") {
                payload.recovery_code = fieldValue;
            } else {
                payload.totp_code = fieldValue;
            }

            setButtonLoading(submitButton, true);

            try {
                const response = await fetch(form.dataset.verifyUrl, {
                    method: "POST",
                    credentials: "same-origin",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(payload),
                });
                const data = await response.json().catch(() => ({}));
                if (!response.ok) {
                    const message =
                        data && typeof data.message === "string" && data.message
                            ? data.message
                            : "Unable to verify the code.";
                    showFieldError(errorTarget, message);
                    if (data && data.locked) {
                        setTimeout(() => {
                            window.location.href = form.dataset.loginUrl;
                        }, 1500);
                    }
                    return;
                }
                window.location.href = form.dataset.successUrl;
            } catch (error) {
                showFieldError(errorTarget, "Unable to verify the code right now. Please try again.");
            } finally {
                setButtonLoading(submitButton, false);
            }
        });
    };

    if (toggleRecoveryBtn) {
        toggleRecoveryBtn.addEventListener("click", () => toggleSection(true));
    }
    if (toggleTotpBtn) {
        toggleTotpBtn.addEventListener("click", () => toggleSection(false));
    }
    handleFormSubmit(totpForm, "totp");
    handleFormSubmit(recoveryForm, "recovery");
});
