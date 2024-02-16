const modal = document.getElementById("modal");
const openModal = document.querySelector(".open-button");
const closeModal = document.querySelector(".close-button");

openModal.addEventListener("click", () => {
  modal.showModal();
});

closeModal.addEventListener("click", () => {
  modal.close();
});

// document.addEventListener("click", (event) => {
//   if (!event.target.classList.contains("open-button")) {
//     modal.close();
//   }
// });
