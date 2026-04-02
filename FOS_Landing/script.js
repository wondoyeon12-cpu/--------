document.addEventListener("DOMContentLoaded", function () {

    // 1. 헤더 스크롤 배경 불투명도 조절
    const header = document.getElementById("main-header");
    window.addEventListener("scroll", () => {
        if (window.scrollY > 50) {
            header.style.backgroundColor = "rgba(255, 255, 255, 0.95)";
            header.style.boxShadow = "0 2px 10px rgba(0,0,0,0.05)";
        } else {
            header.style.backgroundColor = "rgba(255, 255, 255, 0.8)";
            header.style.boxShadow = "none";
        }
    });

    // 2. Section 4: 프로세스 맵 Hover 하이라이트 연동 로직
    const triggers = document.querySelectorAll(".hover-trigger");
    const actions = document.querySelectorAll(".action-item");

    triggers.forEach(trigger => {
        trigger.addEventListener("mouseenter", function () {
            // 모든 active 클래스 제거
            triggers.forEach(t => t.style.fontWeight = "500");
            triggers.forEach(t => t.style.color = "var(--color-text-slate-600)");
            actions.forEach(a => a.classList.remove("active"));

            // 현재 트리거 및 타겟 활성화
            this.style.fontWeight = "700";
            this.style.color = "var(--color-primary)";

            const targetId = this.getAttribute("data-target");
            const targetEl = document.getElementById(targetId);
            if (targetEl) targetEl.classList.add("active");
        });

        trigger.addEventListener("mouseleave", function () {
            this.style.fontWeight = "500";
            this.style.color = "";
            const targetId = this.getAttribute("data-target");
            const targetEl = document.getElementById(targetId);
            if (targetEl) targetEl.classList.remove("active");
        });
    });

    // 3. Section 6: 숫자 카운트 애니메이션 (Intersection Observer 활용)
    const counters = document.querySelectorAll(".counter");
    let hasCounted = false;

    const runCounter = () => {
        counters.forEach(counter => {
            const updateCount = () => {
                const target = +counter.getAttribute("data-target");
                const count = +counter.innerText;
                const speed = 200; // 숫자가 올라가는 속도 역산치

                const inc = target / speed;

                if (count < target) {
                    // 정수냐 소수(99.9)냐에 따라 표기 로직 분기
                    if (target % 1 !== 0) {
                        counter.innerText = (count + inc).toFixed(1);
                    } else {
                        counter.innerText = Math.ceil(count + inc);
                    }
                    setTimeout(updateCount, 15);
                } else {
                    counter.innerText = target;
                }
            };
            updateCount();
        });
    };

    const countObserver = new IntersectionObserver((entries, observer) => {
        const entry = entries[0];
        if (entry.isIntersecting && !hasCounted) {
            runCounter();
            hasCounted = true;
            observer.disconnect();
        }
    }, { threshold: 0.5 });

    const resultSection = document.getElementById("result-proof");
    if (resultSection) {
        countObserver.observe(resultSection);
    }
});

// 4. Section 8: 폼 유효성 검사 로직
function validateForm() {
    let isValid = true;

    // 이메일 대신 연락처(전화번호) 정규식 체크 사용
    const phoneInput = document.getElementById("contactInfo");
    const phoneError = document.getElementById("phoneError");
    // 정규식: 010-0000-0000, 02-000-0000 등 허용 (하이픈 포함 혹은 미포함 간단 체크)
    const phonePattern = /^[0-9]{2,3}-?[0-9]{3,4}-?[0-9]{4}$/;

    if (!phonePattern.test(phoneInput.value)) {
        phoneInput.style.borderColor = "var(--color-error)";
        phoneError.style.display = "block";
        isValid = false;
    } else {
        phoneInput.style.borderColor = "var(--color-border)";
        phoneError.style.display = "none";
    }

    // 개인정보 동의 체크
    const privacyAgree = document.getElementById("privacyAgree");
    const agreeError = document.getElementById("agreeError");

    if (!privacyAgree.checked) {
        agreeError.style.display = "block";
        isValid = false;
    } else {
        agreeError.style.display = "none";
    }

    // 통과 시 가상으로 알림 띄우기
    if (isValid) {
        // 원래는 서버 전송 로직이 들어갈 곳
        alert("운영 체계 진단 요청이 성공적으로 접수되었습니다. 담당자가 곧 연락드리겠습니다!");
        document.getElementById("contactForm").reset();
    }
}
