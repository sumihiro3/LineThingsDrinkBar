
Vue.component('bar-chart', {
    extends: VueChartJs.Bar,

    props: {
        graph_data: {
            type: Object,
            default: null
        }
    },
    async mounted () {
        this.renderChart(
            this.graph_data,
            this.get_graph_options()
        )
    },
    methods: {
        get_graph_options: function () {
            return {
                responsive: true,
                title: {
                    display: true,
                    text: '売上推移',
                    fontSize: 20
                },
                legend: {
                    display: true,
                    position: 'bottom'
                },
                scales: {
                    xAxes: [{
                        stacked: true,
                        scaleLabel: {
                            display: true,
                            labelString: '日',
                            fontSize: 18
                        }
                    }],
                    yAxes: [{
                        stacked: true,
                        ticks: {
                            min: 0,
                            userCallback: function (tick) {
                                return tick.toString() + '円';
                            }
                        },
                        scaleLabel: {
                            display: true,
                            labelString: '売上',
                            fontSize: 18
                        }
                    }]
                },
                layout: {
                    padding: {
                        left: 50,
                        right: 50,
                        top: 0,
                        bottom: 0
                    }
                }
            }
        }
    }

})


const app = new Vue({
    el: '#app',
    template: '#drink_bar',
    delimiters: ['[[', ']]'], // Flaskのdelimiterとの重複を回避
    data: {
        api_loading: false,
        order_graph_mode: 'all',
        purchase_orders: null,
        graph_data: {
            labels: ["1月", "2月", "3月", "4月", "5月"],
            datasets: [
                {
                    label: 'Printer',
                    data: [880, 740, 900, 520, 930],
                    backgroundColor: 'rgba(255, 100, 100, 1)'
                },
                {
                    label: 'PC',
                    data: [1200, 1350, 1220, 1220, 1420],
                    backgroundColor: 'rgba(100, 100, 255, 1)'
                }
            ]
        }
    },
    methods: {
        initVConsole: async function() {
            window.vConsole = new window.VConsole({
                defaultPlugins: ['system', 'network', 'element', 'storage'],
                maxLogNumber: 1000,
                onReady: function () {
                    console.log('vConsole is ready.')
                    console.log('transaction_id: ', this.transaction_id)
                },
                onClearLog: function () {
                    console.log('on clearLog')
                }
            })
        },
        initializeApp: async function() {
            console.log('function initializedLiff called!')
            this.initVConsole()
            // 注文情報を取得する
            await this.gerPurchaseOrders()
            // 注文情報をグラフ表示用データに変換してグラフ表示する
            this.convertGraphData()
            this.api_loading = false
        },
        gerPurchaseOrders: async function() {
            console.log(`gerPurchaseOrders called!`)
            // API実行
            const api_url = `/api/purchase_orders`
            const response = await axios.get(api_url).catch(error => {
                console.error('API GET purchaseOrders failed...')
                console.error(error)
                this.purchase_orders = null
            })
            console.log('API response: ', response)
            this.purchase_orders = response.data.purchase_orders
        },
        convertGraphData: function() {
            console.log("convertGraphData called")
            if (this.order_graph_mode === 'all') {
                this.graph_data = this.convertGraphDataForAll(this.purchase_orders)
            }
        },
        convertGraphDataForAll: function(purchase_orders) {
            console.log("convertGraphDataForAll called")
            // ソートしやすいように注文データを整形する
            const order_list = []
            const date_set = new Set()
            const item_set = new Set()
            for (let i = 0; i < purchase_orders.length ; i++) {
                let order = purchase_orders[i]
                // console.log(`Order: ${order}`)
                let ordered_at = this.unixTimeToDate(order.ordered_at)
                let ordered_at_string = this.formatDateToString(ordered_at)
                let order_data = {
                    'ordered_at': ordered_at_string,
                    'item': order.title,
                    'amount': order.amount
                }
                order_list.push(order_data)
                date_set.add(ordered_at_string)
                item_set.add(order.title)
            }
            // 日付をソート
            const date_list = Array.from(date_set)
            date_list.sort(function (a, b) {
                return (a > b ? 1 : -1)
            })
            console.log(`Converted date_list: ${JSON.stringify(date_list)}`)
            // 商品一覧
            const item_list = Array.from(item_set)
            // 日単位での商品別売上合計を出す
            const ordered_amount_by_date_and_item = {}  // 商品名をキーに、日単位での売上合計のリストをセットする
            for (let i = 0; i < date_list.length; i++) {
                let dt = date_list[i]
                // 同一日付の注文情報のみ抽出
                let orders_by_date = order_list.filter(function(order) {
                    return order.ordered_at === dt
                })
                for (let j = 0; j < item_list.length; j++) {
                    let item = item_list[j]
                    // 商品ごとに抽出
                    let orders_by_date_and_item = orders_by_date.filter(function (order) {
                        return order.item === item
                    })
                    // 日単位での商品別売上合計
                    let amount_list = ordered_amount_by_date_and_item[item]
                    if (!amount_list) {
                        amount_list = []
                    }
                    amount_list.push(this.sumOrderAmount(orders_by_date_and_item))
                    ordered_amount_by_date_and_item[item] = amount_list
                }
            }
            console.log(`ordered_amount_by_date_and_item: ${JSON.stringify(ordered_amount_by_date_and_item)}`)
            // Chart.js 用のグラフデータに変換する
            const graph_data = {
                labels: date_list,
                datasets: this.convertOrderByDateAndItemToDatasets(ordered_amount_by_date_and_item)
            }
            console.log(`GraphData: ${JSON.stringify(graph_data)}`)
            return graph_data
        },
        sumOrderAmount: function(orders) {
            let sum = 0
            orders.forEach(function(o) {
                sum += o.amount;
            })
            return sum
        },
        convertOrderByDateAndItemToDatasets: function(ordersByDateAndItem) {
            console.log(`convertOrderByDateAndItemToDatasets: ${JSON.stringify(ordersByDateAndItem)}`)
            let datasets = []
            for (let item in ordersByDateAndItem) {
                let dataset = {
                    label: item,
                    data: ordersByDateAndItem[item],
                    backgroundColor: this.colorPicker(item)
                }
                datasets.push(dataset)
            }
            return datasets
        },
        colorPicker: function(item_name){
            const default_colors = {
                '麦茶': 'maroon',
                'オレンジジュース': 'orange',
                'コーラ': '#ed1c16',
            }
            let result = default_colors[item_name]
            if (!result) {
                const max = 255
                const min = 0
                let i = 0
                let colorArray = []
                while(i < 3){
                    // 0~255までの乱数を出す
                    let num = Math.floor( Math.random() * (max + 1 - min) ) + min ;
                    colorArray.push(num);
                    i++;
                }
                result = 'rgba('+colorArray+', 1)'
            }
            return result
        },
        unixTimeToDate: function(unix_time) {
            // console.log(`unixTimeToDate called: ${unix_time}`)
            let d = new Date(unix_time * 1000)
            let year  = d.getFullYear()
            let month = d.getMonth()
            let day  = d.getDate()
            return new Date(d.getFullYear(), d.getMonth(), d.getDate(), 0, 0, 0, 0)
        },
        formatDateToString: function(dt) {
            let y = dt.getFullYear()
            let m = ("00" + (dt.getMonth() + 1)).slice(-2)
            let d = ("00" + dt.getDate()).slice(-2)
            return y + "/" + m + "/" + d
        }
    },
    computed: {
    },
    mounted: function() {
        this.api_loading = true
        this.initializeApp()
    }
});

