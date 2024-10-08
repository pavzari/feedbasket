const modal = document.getElementById("add-feed-modal");
const openModal = document.getElementById("find-feed-button");
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

modal.addEventListener("click", (event) => {
    // Close modal button.
    if (event.target.matches("#close-modal-button")) {
        modal.close();
    }
    // Clicking outside closes the modal.
    if (event.target === modal) {
        modal.close();
    }
});

document.body.addEventListener("click", (event) => {
    if (event.target.matches("#edit-feed-button")) {
        const modal = document.getElementById("edit-feed-modal");
        modal.showModal();
    }
    if (event.target.matches("#close-modal-button")) {
        const modal = document.getElementById("edit-feed-modal");
        modal.close();
    }
});
document.body.addEventListener("showMessage", function(evt) {
    alert(evt.detail.alert);
});
