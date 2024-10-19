document.getElementById('submitForm').addEventListener('submit', () => {
    const $submitBtn = document.getElementById('smt');
    const loaderContainer = document.getElementById('loading-container');
    $submitBtn.setAttribute('disabled', '1');

    let dots = '';
    const maxDots = 3;
    const intervalTime = 500;
    let intervalId = setInterval(() => {
        dots = dots.length < maxDots ? dots + '.' : '';
        $submitBtn.textContent = `처리중${dots}`;
    }, intervalTime);

    loaderContainer.style.display = 'flex';
});
