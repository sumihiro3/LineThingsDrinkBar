import { Bar } from 'vue-chartjs';

const app = new Vue({
    el: '#app',
    template: '#drink_bar',
    delimiters: ['[[', ']]'], // Flaskのdelimiterとの重複を回避
    data: {
        line_user_id: 'dummy-user',
        line_profile: null,
        liff_initialized: false,
        api_loading: false,
        api_result: null,
        liff_version: null,
        app_version: '0.1',
        purchase_orders: null,
        graph_data: {
            labels: [],
            datasets: []
        },
        graph_options: {
            responsive: false,  // canvasサイズ自動設定機能を使わない。HTMLで指定したサイズに固定
            title: {                 // 図のタイトル表示
                display: true,
                fontSize: 20,
                text: "注文情報"
            },
            legend: {                // 凡例の表示位置
                position: 'bottom'
            },
            scales: {
                yAxes: [
                    {
                        ticks: {
                            min: 0
                        }
                    }
                ]
            }
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
        initializedLiff: async function() {
            console.log('function initializedLiff called!')
            this.liff_initialized = true
            this.initVConsole()
            this.liff_version = liff._revision
            // ユーザーのプロフィールを取得し、結果からUserID を取得する
            this.line_profile = await liff.getProfile()
            this.line_user_id = this.line_profile.userId
            // TODO 注文情報を取得する
            this.purchase_orders = await this.gerPurchaseOrders()
            // TODO 注文情報のグラフを表示する
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
                this.api_result = null
                this.api_loading = false
            })
            console.log('API response: ', response)
            this.purchase_orders = response.data.purchase_orders
        },
        convertGraphData: function() {
            console.log("convertGraphData called")
        },
        closeLiffWindow: function() {
            console.log("Closing LIFF page")
            if (this.liff_initialized === true) {
                setTimeout(() => (liff.closeWindow()), 500)
            }
        },
    },
    computed: {
    },
    mounted: function() {
        this.api_loading = true
        // LIFF 初期化
        liff.init(
            () => this.initializedLiff(),
            error => {
                console.error(error)
                this.api_loading = false
            }
        )
    }
});