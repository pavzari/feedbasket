const modal = document.getElementById("add-feed-modal");
const openModal = document.querySelector(".find-feed-button");
const feedForm = document.getElementById("feed-form");
const findFeedUrlInput = document.getElementById("url");
const findFeedForm = document.getElementById("find-feed-form");

// Open the modal
openModal.addEventListener("click", () => {
    modal.showModal();
});

// Clear the modal forms upon closing.
modal.addEventListener("close", () => {
    feedForm.innerHTML = "";
    findFeedUrlInput.value = "";
});

// Clear error messages or add feed form if searching again.
findFeedForm.addEventListener("submit", () => {
    feedForm.innerHTML = "";
});

// Close modal button.
modal.addEventListener("click", (event) => {
    if (event.target.matches(".close-button")) {
        modal.close();
    }
});

// Clicking outside closes the modal.
modal.addEventListener("click", (event) => {
    if (event.target === modal) {
        modal.close();
    }
});
