const onboardingPopup = document
	.querySelector(".eth-overview__balance")
	.querySelector('[role="tooltip"]');

if (onboardingPopup && onboardingPopup.style.display !== "none") {
	onboardingPopup.querySelector("button").click();
	return true;
}

return false;
