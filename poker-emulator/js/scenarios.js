/**
 * Конфигурация тестовых сценариев
 * Каждый сценарий содержит последовательность шагов (улиц)
 * 
 * Доступные типы действий:
 * - 'fold' - сбросить карты
 * - 'check' - чек
 * - 'call' - колл
 * - 'bet' - ставка
 * - 'raise' - рейз/3бет
 * 
 * Позиции кнопок задаются в процентах относительно размера экрана
 * (x: 0-100, y: 0-100)
 * 
 * ПРИМЕЧАНИЕ: Изображения должны быть доступны по URL.
 * Рекомендуется загружать на GitHub Pages или другой хостинг.
 * Используйте configurator.html для создания новых тестов.
 */

const SCENARIOS = {
'my_test': {
    name: 'Новый тест',
    description: '',
    steps: [
        {
            id: 'preflop',
            name: 'Префлоп',
            image: 'https://static.dan-step.com/public/photos/AKs/1_preflop.png',
            instruction: 'Ваше действие на Префлоп?',
            correctAction: {
                type: 'raise',
                label: 'Raise to',
                amount: '',
                size: '100',
                sliderClicks: 3
            },
            buttons: [
                {
                    id: 'bet_100',
                    type: 'bet_100',
                    label: '100%',
                    amount: '',
                    x: 71.1,
                    y: 76.6,
                    width: 40,
                    height: 30
                },
                {
                    id: 'slider_click',
                    type: 'slider_click',
                    label: 'Slider',
                    amount: '',
                    x: 82.6,
                    y: 76.6,
                    width: 40,
                    height: 20,
                    sliderClicks: 3
                },
                {
                    id: 'raise',
                    type: 'raise',
                    label: 'Raise to',
                    amount: '',
                    x: 80.9,
                    y: 84.0,
                    width: 100,
                    height: 60
                }
            ],
            feedback: {
                correct: 'Правильно!',
                incorrect: 'Неправильно.'
            }
        },
    ]
}
};

// Экспорт для использования в других файлах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SCENARIOS;
}
