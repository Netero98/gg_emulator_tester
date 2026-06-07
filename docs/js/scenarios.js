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
    'KJc_preflop_is3bet': {
        name: 'Новый тест',
        description: '',
        steps: [
            {
                id: 'preflop',
                name: 'Префлоп',
                image: 'photos/KJc_preflop_is3bet.png',
                instruction: 'Ваше действие на Префлоп?',
                correctAction: {
                    type: 'raise',
                    label: 'Raise to',
                    amount: '',
                    size: '100',
                    sliderClicks: 4
                },
                buttons: [
                    {
                        id: 'bet_100',
                        type: 'bet_100',
                        label: '100%',
                        amount: '',
                        cx: 1372,
                        cy: 872,
                        width: 60,
                        height: 45
                    },
                    {
                        id: 'slider_click',
                        type: 'slider_click',
                        label: 'Slider',
                        amount: '',
                        cx: 1618,
                        cy: 874,
                        width: 75,
                        height: 25,
                        sliderClicks: 4
                    },
                    {
                        id: 'raise',
                        type: 'raise',
                        label: 'Raise to',
                        amount: '',
                        cx: 1580,
                        cy: 962,
                        width: 150,
                        height: 100
                    }
                ],
                feedback: {
                    correct: 'Правильно!',
                    incorrect: 'Неправильно.'
                }
            },
        ]
    },
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
                        cx: 1364,
                        cy: 826,
                        width: 40,
                        height: 30
                    },
                    {
                        id: 'slider_click',
                        type: 'slider_click',
                        label: 'Slider',
                        amount: '',
                        cx: 1584,
                        cy: 826,
                        width: 40,
                        height: 20,
                        sliderClicks: 3
                    },
                    {
                        id: 'raise',
                        type: 'raise',
                        label: 'Raise to',
                        amount: '',
                        cx: 1552,
                        cy: 906,
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
