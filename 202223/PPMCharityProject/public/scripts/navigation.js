function toggleDropdown() {
    document.getElementsByClassName("dropdown-items")[0].classList.toggle("dropdown-items--show");
}

window.addEventListener("resize", () => {
    if (window.innerWidth >= 1010) {
        if (document.getElementsByClassName("dropdown-items")[0].classList.contains("dropdown-items--show")) {
            document.getElementsByClassName("dropdown-items")[0].classList.remove("dropdown-items--show");
        }
    }
});
