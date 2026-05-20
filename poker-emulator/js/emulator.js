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
        this.selectedSize = null; // Выбранный размер ставки
        this.sliderClicks = null; // Количество кликов по ползунку
        this.currentStepActions = []; // Действия на текущем шаге

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
            sizeDisplay: document.getElementById('selected-size-display'),
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

            // Сбрасываем выбранный размер для нового шага
            this.selectedSize = null;
            this.sliderClicksCount = 0;
            this.currentStepActions = [];

            // Сбрасываем отображение выбранного размера
            if (this.elements.sizeDisplay) {
                this.elements.sizeDisplay.textContent = '';
            }

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
        const sizeTypes = ['bet_33', 'bet_50', 'bet_75', 'bet_100'];
        const actionTypes = ['fold', 'check', 'call', 'bet', 'raise'];

        // Если нажата кнопка базового сайза (33%, 50%, 75%, 100%)
        if (sizeTypes.includes(buttonConfig.type)) {
            this.selectedSize = buttonConfig.type;
            // Сбрасываем счетчик кликов по ползунку при смене базового сайза
            this.sliderClicksCount = 0;

            // Показываем, что сайз выбран
            let sizeLabel = buttonConfig.label;
            
            // Обновляем отображение выбранного размера
            if (this.elements.sizeDisplay) {
                this.elements.sizeDisplay.textContent = `Размер: ${sizeLabel}`;
            }
            
            this.elements.resultDisplay.className = 'result waiting';
            this.elements.resultDisplay.textContent = `Выбран размер: ${sizeLabel}. Теперь выберите действие (Bet/Raise) или настройте ползунком.`;
            console.log(`[TEST] Выбран базовый размер: ${buttonConfig.type}`);
            return;
        }

        // Если нажата кнопка ползунка - увеличиваем счетчик кликов
        if (buttonConfig.type === 'slider_click') {
            this.sliderClicksCount = (this.sliderClicksCount || 0) + 1;
            
            // Показываем текущее количество кликов
            let sizeLabel = this.selectedSize ? 
                step.buttons.find(b => b.type === this.selectedSize)?.label || '' : 
                'Custom';
            sizeLabel += ` + Slider (${this.sliderClicksCount}× клик)`;
            
            // Обновляем отображение выбранного размера
            if (this.elements.sizeDisplay) {
                this.elements.sizeDisplay.textContent = `Размер: ${sizeLabel}`;
            }
            
            this.elements.resultDisplay.className = 'result waiting';
            this.elements.resultDisplay.textContent = `Добавлено ${this.sliderClicksCount} кликов по ползунку. Выберите действие (Bet/Raise).`;
            console.log(`[TEST] Клик по ползунку: ${this.sliderClicksCount} раз`);
            return;
        }

        // Если нажата кнопка действия (Fold/Check/Call/Bet/Raise)
        if (actionTypes.includes(buttonConfig.type)) {
            // Проверяем правильность
            const expectedSize = step.correctAction.size;
            const expectedSliderClicks = step.correctAction.sliderClicks || 0;
            const expectedAction = step.correctAction.type;

            // Проверяем действие
            const isActionCorrect = buttonConfig.type === expectedAction;

            // Проверяем базовый размер
            let isBaseSizeCorrect = true;
            if (expectedSize) {
                // В сценарии указан сайз - он должен быть выбран и совпадать
                isBaseSizeCorrect = this.selectedSize === `bet_${expectedSize}`;
            } else {
                // В сценарии сайз не указан - его не должно быть
                isBaseSizeCorrect = !this.selectedSize;
            }

            // Проверяем количество кликов по ползунку
            const actualSliderClicks = this.sliderClicksCount || 0;
            const isSliderClicksCorrect = actualSliderClicks === expectedSliderClicks;

            const isSizeCorrect = isBaseSizeCorrect && isSliderClicksCorrect;
            const sizeError = !isSizeCorrect;

            const isCorrect = isActionCorrect && isSizeCorrect;

            // Блокируем дальнейшие действия
            this.isWaitingForAction = false;

            // Формируем описание действия
            let actionDesc = '';
            if (this.selectedSize) {
                const sizeBtn = step.buttons.find(b => b.type === this.selectedSize);
                if (sizeBtn) {
                    actionDesc = sizeBtn.label;
                }
            }
            if (actualSliderClicks > 0) {
                actionDesc += (actionDesc ? ' + ' : '') + `Slider (${actualSliderClicks}×)`;
            }
            actionDesc = actionDesc ? `${actionDesc} → ` : '';
            actionDesc += buttonConfig.label;
            if (buttonConfig.amount) {
                actionDesc += ` ${buttonConfig.amount}`;
            }

            // Формируем описание ожидаемого действия
            let expectedDesc = '';
            if (expectedSize) {
                expectedDesc = `${expectedSize}%`;
            }
            if (expectedSliderClicks > 0) {
                expectedDesc += (expectedDesc ? ' + ' : '') + `Slider (${expectedSliderClicks}×)`;
            }
            expectedDesc = expectedDesc ? `${expectedDesc} → ` : '';
            expectedDesc += step.correctAction.label;
            if (step.correctAction.amount) {
                expectedDesc += ` ${step.correctAction.amount}`;
            }

            // Сохраняем результат
            this.results.push({
                step: step.name,
                action: actionDesc,
                correct: isCorrect,
                expected: expectedDesc,
                actionType: buttonConfig.type,
                expectedType: expectedAction,
                selectedSize: this.selectedSize,
                expectedSize: expectedSize,
                sliderClicks: actualSliderClicks,
                expectedSliderClicks: expectedSliderClicks,
                sizeError: sizeError
            });

            // Показываем результат теста
            if (isCorrect) {
                this.elements.resultDisplay.className = 'result correct';
                this.elements.resultDisplay.textContent = `✓ ${step.feedback.correct}`;
                console.log(`[TEST] ✓ Правильно: ${actionDesc}`);
            } else {
                this.elements.resultDisplay.className = 'result incorrect';
                if (sizeError) {
                    if (expectedSize && !this.selectedSize) {
                        this.elements.resultDisplay.textContent = `✗ Не выбран базовый сайз (${expectedSize}%). ${step.feedback.incorrect}`;
                    } else if (!expectedSize && this.selectedSize) {
                        this.elements.resultDisplay.textContent = `✗ Выбран лишний сайз. В сценарии сайз не требуется. ${step.feedback.incorrect}`;
                    } else if (!isBaseSizeCorrect) {
                        const actualSize = this.selectedSize ? this.selectedSize.replace('bet_', '') : 'не выбран';
                        this.elements.resultDisplay.textContent = `✗ Неправильный базовый сайз: ${actualSize}% вместо ${expectedSize}%. ${step.feedback.incorrect}`;
                    } else if (!isSliderClicksCorrect) {
                        if (expectedSliderClicks > 0 && actualSliderClicks === 0) {
                            this.elements.resultDisplay.textContent = `✗ Не нажат ползунок (нужно ${expectedSliderClicks} кликов). ${step.feedback.incorrect}`;
                        } else if (expectedSliderClicks === 0 && actualSliderClicks > 0) {
                            this.elements.resultDisplay.textContent = `✗ Лишние клики по ползунку (${actualSliderClicks}, а нужно 0). ${step.feedback.incorrect}`;
                        } else {
                            this.elements.resultDisplay.textContent = `✗ Неправильное количество кликов по ползунку: ${actualSliderClicks} вместо ${expectedSliderClicks}. ${step.feedback.incorrect}`;
                        }
                    } else {
                        this.elements.resultDisplay.textContent = `✗ Неправильный размер ставки. ${step.feedback.incorrect}`;
                    }
                } else {
                    this.elements.resultDisplay.textContent = `✗ Неправильное действие. Ожидалось: ${step.correctAction.label}. ${step.feedback.incorrect}`;
                }
                console.log(`[TEST] ✗ Неправильно: ${actionDesc}, ожидалось: ${expectedDesc}`);
            }

            // Показываем подсказку с правильным действием
            this.showActionHint(step.correctAction);

            // Разблокируем кнопку "Следующий шаг"
            this.elements.nextBtn.disabled = false;

            // Сбрасываем отображение размера после завершения хода
            if (this.elements.sizeDisplay) {
                this.elements.sizeDisplay.textContent = '';
            }

            // Если это последний шаг, показываем итоги
            if (this.currentStepIndex === this.currentScenario.steps.length - 1) {
                setTimeout(() => this.showSummary(), 1500);
            }
        }
    }

    showActionHint(correctAction) {
        const hint = this.elements.actionHint;

        // Формируем текст подсказки
        let actionText = '';
        
        // Добавляем базовый размер (если есть)
        if (correctAction.size) {
            actionText = `${correctAction.size}%`;
        }
        
        // Добавляем клики по ползунку (если есть)
        if (correctAction.sliderClicks && correctAction.sliderClicks > 0) {
            actionText += (actionText ? ' + ' : '') + `Slider (${correctAction.sliderClicks}×)`;
        }
        
        // Добавляем стрелку и действие
        actionText = actionText ? `${actionText} → ` : '';
        actionText += `${correctAction.label} ${correctAction.amount || ''}`;

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
            let errorDetail = '';
            if (!result.correct && result.sizeError) {
                if (result.selectedSize !== `bet_${result.expectedSize}`) {
                    errorDetail = '<br><span style="color: #ff8888;">⚠ Ошибка в базовом размере</span>';
                } else if (result.sliderClicks !== result.expectedSliderClicks) {
                    errorDetail = `<br><span style="color: #ff8888;">⚠ Ползунок: ${result.sliderClicks} вместо ${result.expectedSliderClicks} кликов</span>`;
                } else {
                    errorDetail = '<br><span style="color: #ff8888;">⚠ Ошибка в размере ставки</span>';
                }
            }
            html += `
                <div class="summary-item ${result.correct ? 'correct' : 'incorrect'}">
                    <div>
                        <span class="step-name">${index + 1}. ${result.step}</span>
                        <div class="action-taken">
                            ${result.correct ? '✓' : '✗'} Ваше действие: ${result.action}
                            ${!result.correct ? `<br>✓ Правильно: ${result.expected}${errorDetail}` : ''}
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
