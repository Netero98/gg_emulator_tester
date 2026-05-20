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
    'AKs': {
        name: 'AKs',
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
                    amount: ''
                },
                buttons: [
                    {
                        id: 'raise',
                        type: 'raise',
                        label: 'Raise to',
                        amount: '',
                        x: 80.9,
                        y: 84.2,
                        width: 100,
                        height: 60
                    }
                ],
                feedback: {
                    correct: 'Правильно!',
                    incorrect: 'Неправильно.'
                }
            },
            {
                id: 'flop',
                name: 'Флоп',
                image: 'https://static.dan-step.com/public/photos/AKs/2_flop.png',
                instruction: 'Ваше действие на Флоп?',
                correctAction: {
                    type: 'bet',
                    label: 'Bet',
                    amount: ''
                },
                buttons: [
                    {
                        id: 'bet',
                        type: 'bet',
                        label: 'Bet',
                        amount: '',
                        x: 80.8,
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
            {
                id: 'turn',
                name: 'Турн',
                image: 'https://static.dan-step.com/public/photos/AKs/3_turn.png',
                instruction: 'Ваше действие на Турн?',
                correctAction: {
                    type: 'check',
                    label: 'Check',
                    amount: ''
                },
                buttons: [
                    {
                        id: 'check',
                        type: 'check',
                        label: 'Check',
                        amount: '',
                        x: 72.1,
                        y: 84.2,
                        width: 100,
                        height: 60
                    }
                ],
                feedback: {
                    correct: 'Правильно!',
                    incorrect: 'Неправильно.'
                }
            },
            {
                id: 'river',
                name: 'Ривер',
                image: 'https://static.dan-step.com/public/photos/AKs/4_reaver.png',
                instruction: 'Ваше действие на Ривер?',
                correctAction: {
                    type: 'fold',
                    label: 'Fold',
                    amount: ''
                },
                buttons: [
                    {
                        id: 'fold',
                        type: 'fold',
                        label: 'Fold',
                        amount: '',
                        x: 63.6,
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
    // Сценарий: AKs - 3бет префлоп -> цбет флоп -> чек турн -> фолд ривер
    // 'aks_3bet_cbet': {
    //     name: 'AKs - 3бет -> цбет -> чек -> фолд',
    //     description: 'Тест на правильную линию с AKs в 3бет поте',
    //     steps: [
    //         {
    //             id: 'preflop',
    //             name: 'Префлоп',
    //             image: 'https://github.com/Netero98/poker_photos/blob/master/AKs/1_preflop.png',
    //             instruction: 'Вы на ББ с AKs. Оппонент открылся с баттона. Ваше действие?',
    //             correctAction: {
    //                 type: 'raise',
    //                 label: 'Raise',
    //                 amount: '$0.08'
    //             },
    //             buttons: [
    //                 {
    //                     id: 'fold',
    //                     type: 'fold',
    //                     label: 'Fold',
    //                     x: 74.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 },
    //                 {
    //                     id: 'call',
    //                     type: 'call',
    //                     label: 'Call',
    //                     amount: '$0.02',
    //                     x: 84.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 },
    //                 {
    //                     id: 'raise',
    //                     type: 'raise',
    //                     label: 'Raise to',
    //                     amount: '$0.08',
    //                     x: 94.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 }
    //             ],
    //             feedback: {
    //                 correct: 'Отлично! С AKs нужно делать 3бет для велью и защиты блайндов.',
    //                 incorrect: 'Неправильно. С AKs на ББ против открытия с баттона нужно делать 3бет.'
    //             }
    //         },
    //         {
    //             id: 'flop',
    //             name: 'Флоп',
    //             image: 'images/flop.png',
    //             instruction: 'Флоп: 8♠ 10♦ Q♣. Вы инициатор 3бета. Ваше действие?',
    //             correctAction: {
    //                 type: 'bet',
    //                 label: 'Bet',
    //                 amount: '$0.02'
    //             },
    //             buttons: [
    //                 {
    //                     id: 'fold',
    //                     type: 'fold',
    //                     label: 'Fold',
    //                     x: 74.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 },
    //                 {
    //                     id: 'check',
    //                     type: 'check',
    //                     label: 'Check',
    //                     x: 84.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 },
    //                 {
    //                     id: 'bet',
    //                     type: 'bet',
    //                     label: 'Bet',
    //                     amount: '$0.02',
    //                     x: 94.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 }
    //             ],
    //             feedback: {
    //                 correct: 'Верно! Нужно продолжать агрессию с оверкартами и гатшотом.',
    //                 incorrect: 'Неправильно. Как инициатор 3бета нужно делать цбет с оверкартами и гатшотом.'
    //             }
    //         },
    //         {
    //             id: 'turn',
    //             name: 'Турн',
    //             image: 'images/turn.png',
    //             instruction: 'Турн: 9♦. Оппонент чекает. Ваше действие?',
    //             correctAction: {
    //                 type: 'check',
    //                 label: 'Check'
    //             },
    //             buttons: [
    //                 {
    //                     id: 'fold',
    //                     type: 'fold',
    //                     label: 'Fold',
    //                     x: 74.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 },
    //                 {
    //                     id: 'check',
    //                     type: 'check',
    //                     label: 'Check',
    //                     x: 84.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 },
    //                 {
    //                     id: 'bet',
    //                     type: 'bet',
    //                     label: 'Bet',
    //                     amount: '$0.02',
    //                     x: 94.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 }
    //             ],
    //             feedback: {
    //                 correct: 'Правильно! На чек опа с двумя оверкартами и незавершённым гатшотом лучше контролировать пот.',
    //                 incorrect: 'Неправильно. После чека оппонента на такой карте лучше контролировать пот.'
    //             }
    //         },
    //         {
    //             id: 'river',
    //             name: 'Ривер',
    //             image: 'images/river.png',
    //             instruction: 'Ривер: 4♣. Оппонент ставит $0.27. Ваше действие?',
    //             correctAction: {
    //                 type: 'fold',
    //                 label: 'Fold'
    //             },
    //             buttons: [
    //                 {
    //                     id: 'fold',
    //                     type: 'fold',
    //                     label: 'Fold',
    //                     x: 74.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 },
    //                 {
    //                     id: 'call',
    //                     type: 'call',
    //                     label: 'Call',
    //                     amount: '$0.27',
    //                     x: 84.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 },
    //                 {
    //                     id: 'raise',
    //                     type: 'raise',
    //                     label: 'Raise to',
    //                     amount: '$0.54',
    //                     x: 94.5,
    //                     y: 88.5,
    //                     width: 140,
    //                     height: 65
    //                 }
    //             ],
    //             feedback: {
    //                 correct: 'Верно! У оппонента слишком много вэлью, с одними оверкартами фолд - правильное решение.',
    //                 incorrect: 'Неправильно. Оппонент показывает силу, с одними оверкартами нужно сбросить.'
    //             }
    //         }
    //     ]
    // }
};

// Экспорт для использования в других файлах
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SCENARIOS;
}
