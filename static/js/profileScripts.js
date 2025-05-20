// Add subtle animation to stat cards on page load
document.addEventListener('DOMContentLoaded', function() {
    const statCards = document.querySelectorAll('.stat-card');
    statCards.forEach((card, index) => {
        setTimeout(() => {
            card.style.transform = 'translateY(0)';
            card.style.opacity = '1';
        }, index * 150);
    });
});

function clearProfilePicture() {
    // Set default profile picture preview
    document.getElementById("avatarPreview").src = "/media/profile_pics/user_default.png";

    // Clear file input
    let fileInput = document.getElementById("id_profile_picture");
    let newFileInput = fileInput.cloneNode(true);
    fileInput.parentNode.replaceChild(newFileInput, fileInput);

    // Tell Django to reset the profile picture
    document.getElementById("clear_profile_picture").value = "true";
}

// Real-time avatar preview
document.getElementById('id_profile_picture').addEventListener('change', function(e) {
    const reader = new FileReader();
    reader.onload = function() {
        document.getElementById('avatarPreview').src = reader.result;
    }
    reader.readAsDataURL(e.target.files[0]);
});

// Add floating label animation
document.querySelectorAll('.form-input').forEach(input => {
    input.addEventListener('focus', function() {
        this.previousElementSibling.style.color = '#00f3ff';
    });
    input.addEventListener('blur', function() {
        if (!this.value) {
            this.previousElementSibling.style.color = '#666';
        }
    });
});

// Add input styling
document.querySelectorAll('input, textarea, select').forEach(element => {
    element.classList.add('form-input');
});