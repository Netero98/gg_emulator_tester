/**
 * Poker Emulator - Основной класс для управления тестированием
 * 
 * Использует невидимые прозрачные области поверх скриншота для отслеживания кликов.
 * Это позволяет боту "видеть" оригинальные кнопки на скриншоте и кликать по ним.
 */
class PokerEmulator {
    constructor() {
        this.currentScenario = null;
        this.currentStepIndex = 0;
        this.results = [];
        this.isWaitingForAction = true;
        this.debugMode = false;
        
        this.initElements();
        this.initEventListeners();
        
        // Загружаем первый доступный сценарий
        const firstScenarioId = Object.keys(SCENARIOS)[0];
        if (firstScenarioId) {
            this.loadScenario(firstScenarioId);
        }
    }

    initElements() {
        this.elements = {
            screenshotImg: document.getElementById('screenshot-img'),
            clickOverlay: document.getElementById('click-overlay'),
            gameScreen: document.getElementById('game-screen'),
            actionHint: document.getElementById('action-hint'),
            currentStep: document.getElementById('current-step'),
            totalSteps: document.getElementById('total-steps'),
            resultDisplay: document.getElementById('result-display'),
            scenarioSelect: document.getElementById('scenario-select'),
            resetBtn: document.getElementById('reset-btn'),
            nextBtn: document.getElementById('next-btn'),
            testSummary: document.getElementById('test-summary'),
            summaryContent: document.getElementById('summary-content'),
            debugCheckbox: document.getElementById('debug-mode')
        };
        
        // Генерируем опции селекта из SCENARIOS
        this.populateScenarioSelect();
    }
    
    populateScenarioSelect() {
        const select = this.elements.scenarioSelect;
        select.innerHTML = ''; // Очищаем
        
        // Проходим по всем сценариям в SCENARIOS
        for (const [id, scenario] of Object.entries(SCENARIOS)) {
            const option = document.createElement('option');
            option.value = id;
            option.textContent = scenario.name || id;
            select.appendChild(option);
        }
    }

    initEventListeners() {
        this.elements.scenarioSelect.addEventListener('change', (e) => {
            this.loadScenario(e.target.value);
        });

        this.elements.resetBtn.addEventListener('click', () => {
            this.resetTest();
        });

        this.elements.nextBtn.addEventListener('click', () => {
            this.nextStep();
        });

        // Режим отладки - показать области клика
        this.elements.debugCheckbox.addEventListener('change', (e) => {
            this.debugMode = e.target.checked;
            if (this.debugMode) {
                this.elements.gameScreen.classList.add('debug');
            } else {
                this.elements.gameScreen.classList.remove('debug');
            }
        });

        // Обработка изменения размера окна для пересчёта позиций
        window.addEventListener('resize', () => {
            if (this.currentScenario) {
                this.renderClickAreas();
            }
        });
    }

    loadScenario(scenarioId) {
        if (!SCENARIOS[scenarioId]) {
            console.error(`Сценарий ${scenarioId} не найден`);
            return;
        }

        this.currentScenario = SCENARIOS[scenarioId];
        this.currentStepIndex = 0;
        this.results = [];
        
        // Обновляем UI
        this.elements.totalSteps.textContent = this.currentScenario.steps.length;
        this.elements.testSummary.style.display = 'none';
        
        this.renderStep();
    }

    renderStep() {
        const step = this.currentScenario.steps[this.currentStepIndex];

        // Обновляем счётчик шагов
        this.elements.currentStep.textContent = this.currentStepIndex + 1;

        // Очищаем предыдущие результаты
        this.elements.resultDisplay.className = 'result waiting';
        this.elements.resultDisplay.textContent = step.instruction;

        // Скрываем подсказку
        this.elements.actionHint.classList.remove('visible');

        // Разблокируем области для кликов
        this.isWaitingForAction = true;

        // Обновляем состояние кнопки "Следующий шаг"
        this.elements.nextBtn.disabled = true;

        // Устанавливаем src изображения и ждем загрузки
        this.elements.screenshotImg.src = step.image;
        this.elements.screenshotImg.onload = () => {
            // Отрисовываем невидимые области кликов только после загрузки изображения
            this.renderClickAreas();
        };
        this.elements.screenshotImg.onerror = () => {
            console.error('Ошибка загрузки изображения:', step.image);
            this.renderClickAreas();
        };
    }

    renderClickAreas() {
        const step = this.currentScenario.steps[this.currentStepIndex];
        this.elements.clickOverlay.innerHTML = '';

        // Используем размеры изображения, а не контейнера
        const imgWidth = this.elements.screenshotImg.offsetWidth;
        const imgHeight = this.elements.screenshotImg.offsetHeight;

        step.buttons.forEach(buttonConfig => {
            const clickArea = this.createClickArea(buttonConfig, imgWidth, imgHeight);
            this.elements.clickOverlay.appendChild(clickArea);
        });
    }

    createClickArea(config, containerWidth, containerHeight) {
        // Создаём невидимую область для клика
        const area = document.createElement('button');
        area.className = 'click-area';
        area.id = `area-${config.id}`;
        area.setAttribute('data-action', config.type);
        area.setAttribute('data-label', config.label);
        area.setAttribute('data-amount', config.amount || '');

        // Для ползунка сохраняем количество кликов
        if (config.type === 'slider_click' && config.sliderClicks) {
            area.setAttribute('data-slider-clicks', config.sliderClicks);
        }

        // Позиционируем область в процентах относительно контейнера
        const left = (config.x / 100) * containerWidth - (config.width / 2);
        const top = (config.y / 100) * containerHeight - (config.height / 2);

        area.style.left = `${left}px`;
        area.style.top = `${top}px`;
        area.style.width = `${config.width}px`;
        area.style.height = `${config.height}px`;

        // Для доступности (screen readers) добавляем aria-label
        let ariaLabel = `${config.label} ${config.amount || ''}`;
        if (config.type === 'slider_click' && config.sliderClicks) {
            ariaLabel += ` (${config.sliderClicks} кликов)`;
        }
        area.setAttribute('aria-label', ariaLabel);

        // Обработчик клика - невидимый для бота, но регистрирует действие
        area.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.handleAction(config);
        });

        // Также поддерживаем touch для мобильных устройств
        area.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.handleAction(config);
        });

        return area;
    }

    handleAction(buttonConfig) {
        if (!this.isWaitingForAction) return;

        const step = this.currentScenario.steps[this.currentStepIndex];
        const isCorrect = buttonConfig.type === step.correctAction.type;

        // Блокируем дальнейшие действия
        this.isWaitingForAction = false;

        // Формируем описание действия
        let actionDesc = buttonConfig.label;
        if (buttonConfig.amount) {
            actionDesc += ` ${buttonConfig.amount}`;
        }
        if (buttonConfig.type === 'slider_click' && buttonConfig.sliderClicks) {
            actionDesc += ` (${buttonConfig.sliderClicks}× клик)`;
        }

        // Формируем описание ожидаемого действия
        let expectedDesc = step.correctAction.label;
        if (step.correctAction.amount) {
            expectedDesc += ` ${step.correctAction.amount}`;
        }
        if (step.correctAction.type === 'slider_click' && step.correctAction.sliderClicks) {
            expectedDesc += ` (${step.correctAction.sliderClicks}× клик)`;
        }

        // Сохраняем результат
        this.results.push({
            step: step.name,
            action: actionDesc,
            correct: isCorrect,
            expected: expectedDesc,
            actionType: buttonConfig.type,
            expectedType: step.correctAction.type
        });

        // Показываем результат теста (только в панели статуса, не на кнопках)
        if (isCorrect) {
            this.elements.resultDisplay.className = 'result correct';
            this.elements.resultDisplay.textContent = `✓ ${step.feedback.correct}`;
            console.log(`[TEST] ✓ Правильно: ${buttonConfig.type}`);
        } else {
            this.elements.resultDisplay.className = 'result incorrect';
            this.elements.resultDisplay.textContent = `✗ ${step.feedback.incorrect}`;
            console.log(`[TEST] ✗ Неправильно: ${buttonConfig.type}, ожидалось: ${step.correctAction.type}`);
        }

        // Показываем подсказку с правильным действием
        this.showActionHint(step.correctAction);

        // Разблокируем кнопку "Следующий шаг"
        this.elements.nextBtn.disabled = false;

        // Если это последний шаг, показываем итоги
        if (this.currentStepIndex === this.currentScenario.steps.length - 1) {
            setTimeout(() => this.showSummary(), 1500);
        }
    }

    showActionHint(correctAction) {
        const hint = this.elements.actionHint;

        // Формируем текст подсказки
        let actionText = `${correctAction.label} ${correctAction.amount || ''}`;
        if (correctAction.type === 'slider_click' && correctAction.sliderClicks) {
            actionText += ` (${correctAction.sliderClicks}× клик)`;
        }

        hint.innerHTML = `
            <div>Правильное действие:</div>
            <div style="font-size: 24px; margin-top: 10px;">${actionText}</div>
        `;
        hint.classList.add('visible');

        // Автоматически скрываем через 3 секунды
        setTimeout(() => {
            hint.classList.remove('visible');
        }, 3000);
    }

    nextStep() {
        if (this.currentStepIndex < this.currentScenario.steps.length - 1) {
            this.currentStepIndex++;
            this.renderStep();
        }
    }

    resetTest() {
        this.currentStepIndex = 0;
        this.results = [];
        this.elements.testSummary.style.display = 'none';
        this.renderStep();
    }

    showSummary() {
        const correctCount = this.results.filter(r => r.correct).length;
        const total = this.results.length;
        
        let html = `
            <div class="summary-score" style="text-align: center; font-size: 24px; margin-bottom: 20px;">
                <span style="color: ${correctCount === total ? '#00ff00' : '#ffd700'};">
                    ${correctCount} / ${total}
                </span> правильных ответов
            </div>
        `;
        
        html += '<div class="summary-list">';
        
        this.results.forEach((result, index) => {
            html += `
                <div class="summary-item ${result.correct ? 'correct' : 'incorrect'}">
                    <div>
                        <span class="step-name">${index + 1}. ${result.step}</span>
                        <div class="action-taken">
                            ${result.correct ? '✓' : '✗'} Ваше действие: ${result.action}
                            ${!result.correct ? `<br>✓ Правильно: ${result.expected}` : ''}
                        </div>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        
        this.elements.summaryContent.innerHTML = html;
        this.elements.testSummary.style.display = 'block';
        
        // Прокручиваем к результатам
        this.elements.testSummary.scrollIntoView({ behavior: 'smooth' });
    }
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.emulator = new PokerEmulator();
});
