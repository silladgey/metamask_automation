"use strict";

const recoveryWords = arguments[0];
const recoveryInputs = document.querySelectorAll(
	"input[data-testid^='recovery-phrase-input-']"
);

recoveryWords.forEach((word, index) => {
	const input = Array.from(recoveryInputs).find((input) =>
		input.dataset.testid.endsWith(`-${index}`)
	);
	if (input) {
		input.setAttribute("value", word);
		input.dispatchEvent(new Event("input", { bubbles: true }));
	}
});
