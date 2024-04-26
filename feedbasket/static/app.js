const modal = document.getElementById("add-feed-modal");
const openModal = document.querySelector(".find-feed-button");
const closeModal = document.querySelector(".close-button");
const feedForm = document.getElementById("feed-form");
const findFeedUrlInput = document.getElementById("url");

// return the modal to initial state upon closing.
modal.addEventListener("close", () => {
    feedForm.innerHTML = "";
    findFeedUrlInput.value = "";
});

openModal.addEventListener("click", () => {
    modal.showModal();
});

// closeModal.addEventListener("click", () => {
//     modal.close();
// });

modal.addEventListener("click", (event) => {
    if (event.target === modal) {
        modal.close();
    }
});
