const modal = document.getElementById("add-feed-modal");
const openModal = document.querySelector(".find-feed-button");
const closeModal = document.querySelector(".close-button");
const feedForm = document.getElementById("feed-form");

// return the modal to initial state upon closing.
modal.addEventListener("close", () => {
    feedForm.innerHTML = "";
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
