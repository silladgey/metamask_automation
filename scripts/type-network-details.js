const network = arguments[0];

const popup = document.querySelector("section[role='dialog']");
const inputs = Array.from(popup.querySelectorAll("input[type='text'][id]"));

const networkNameInput = popup.querySelector("#networkName");
const networkChainIdInput = popup.querySelector("#chainId");
const networkCurrencySymbolInput = popup.querySelector("#nativeCurrency");

if (networkNameInput) {
	networkNameInput.setAttribute("value", network.name);
	networkNameInput.dispatchEvent(new Event("input", { bubbles: true }));
}

if (networkChainIdInput) {
	networkChainIdInput.setAttribute("value", network.chain_id);
	networkChainIdInput.dispatchEvent(new Event("input", { bubbles: true }));
}

if (networkCurrencySymbolInput) {
	networkCurrencySymbolInput.setAttribute("value", network.currency_symbol);
	networkCurrencySymbolInput.dispatchEvent(
		new Event("input", { bubbles: true })
	);
}
