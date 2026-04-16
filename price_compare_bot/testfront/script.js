// 全局状态
let appState = {
    loggedIn: {
        taobao: false,
        xianyu: false,
        wajueji: false,
        hpoi: true // HPOI不需要登录
    },
    currentSearch: '',
    searchResults: [],
    hpoiBestResult: null,
    hpoiRecommendations: [],
    isLoading: false
};

// DOM元素
const elements = {
    // 登录相关
    loginBtn: document.getElementById('loginBtn'),
    refreshStatusBtn: document.getElementById('refreshStatusBtn'),
    loginModal: document.getElementById('loginModal'),
    closeModalBtn: document.getElementById('closeModalBtn'),
    cancelLoginBtn: document.getElementById('cancelLoginBtn'),
    confirmLoginBtn: document.getElementById('confirmLoginBtn'),
    loginProgressFill: document.getElementById('loginProgressFill'),
    
    // 搜索相关
    searchInput: document.getElementById('searchInput'),
    searchBtn: document.getElementById('searchBtn'),
    freeShippingFirst: document.getElementById('freeShippingFirst'),
    
    // 结果显示相关
    resultsSection: document.getElementById('resultsSection'),
    resultsContainer: document.getElementById('resultsContainer'),
    resultsCount: document.getElementById('resultsCount'),
    sortIndicator: document.getElementById('sortIndicator'),
    
    // HPOI相关
    hpoiBestSection: document.getElementById('hpoiBestSection'),
    hpoiBestCard: document.getElementById('hpoiBestCard'),
    hpoiRecommendationsSection: document.getElementById('hpoiRecommendationsSection'),
    recommendationsContainer: document.getElementById('recommendationsContainer'),
    
    // 加载相关
    loadingOverlay: document.getElementById('loadingOverlay'),
    loadingMessage: document.getElementById('loadingMessage')
};

// 平台状态元素映射
const platformStatusElements = {
    taobao: document.querySelector('.platform-status[data-platform="taobao"]'),
    xianyu: document.querySelector('.platform-status[data-platform="xianyu"]'),
    wajueji: document.querySelector('.platform-status[data-platform="wajueji"]'),
    hpoi: document.querySelector('.platform-status[data-platform="hpoi"]')
};

// API端点
const API_ENDPOINTS = {
    checkLogin: '/api/check-login',
    login: '/api/login',
    search: '/api/search',
    getStatus: '/api/status'
};

// 工具函数
const utils = {
    // 显示加载指示器
    showLoading(message = '正在处理，请稍候...') {
        appState.isLoading = true;
        elements.loadingMessage.textContent = message;
        elements.loadingOverlay.style.display = 'flex';
    },

    // 隐藏加载指示器
    hideLoading() {
        appState.isLoading = false;
        elements.loadingOverlay.style.display = 'none';
    },

    // 显示错误消息
    showError(message) {
        alert(`错误: ${message}`);
    },

    // 格式化价格
    formatPrice(price) {
        if (typeof price === 'string') {
            price = parseFloat(price) || 0;
        }
        return `¥${price.toFixed(2)}`;
    },

    // 高亮搜索词
    highlightSearchText(text, searchTerm) {
        if (!searchTerm) return text;
        const regex = new RegExp(`(${searchTerm})`, 'gi');
        return text.replace(regex, '<span class="highlight">$1</span>');
    },

    // 获取平台图标
    getPlatformIcon(platform) {
        const icons = {
            taobao: 'fas fa-shopping-cart',
            xianyu: 'fas fa-fish',
            wajueji: 'fas fa-gem',
            hpoi: 'fas fa-star'
        };
        return icons[platform] || 'fas fa-question';
    },

    // 获取平台中文名称
    getPlatformName(platform) {
        const names = {
            taobao: '淘宝',
            xianyu: '闲鱼',
            wajueji: '挖煤姬',
            hpoi: 'HPOI'
        };
        return names[platform] || platform;
    },

    // 获取平台颜色类
    getPlatformColorClass(platform) {
        return platform;
    }
};

// 登录功能
const loginManager = {
    // 更新平台状态显示
    updatePlatformStatus() {
        for (const [platform, isLoggedIn] of Object.entries(appState.loggedIn)) {
            const element = platformStatusElements[platform];
            if (!element) continue;

            const statusDot = element.querySelector('.status-dot');
            const statusText = element.querySelector('.status-text');

            if (isLoggedIn) {
                statusDot.className = 'status-dot status-online';
                statusText.textContent = '已登录';
            } else {
                statusDot.className = 'status-dot status-offline';
                statusText.textContent = platform === 'hpoi' ? '无需登录' : '未登录';
            }
        }
    },

    // 检查登录状态
    async checkLoginStatus() {
        try {
            utils.showLoading('正在检查登录状态...');
            const response = await fetch(API_ENDPOINTS.checkLogin);
            const data = await response.json();

            if (data.success) {
                appState.loggedIn = {
                    ...appState.loggedIn,
                    ...data.status
                };
                this.updatePlatformStatus();
            }
        } catch (error) {
            console.error('检查登录状态失败:', error);
        } finally {
            utils.hideLoading();
        }
    },

    // 开始登录流程
    async startLogin() {
        // 显示登录模态框
        elements.loginModal.style.display = 'flex';
        
        // 重置进度条
        elements.loginProgressFill.style.width = '0%';
    },

    // 执行登录
    async performLogin() {
        try {
            // 更新进度条
            elements.loginProgressFill.style.width = '33%';
            
            utils.showLoading('正在启动登录流程...');
            
            // 调用登录API
            const response = await fetch(API_ENDPOINTS.login, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    platforms: ['taobao', 'xianyu', 'wajueji']
                })
            });

            const data = await response.json();

            if (data.success) {
                // 更新进度条
                elements.loginProgressFill.style.width = '66%';
                
                // 等待一段时间让用户完成登录
                await new Promise(resolve => setTimeout(resolve, 5000));
                
                // 更新进度条
                elements.loginProgressFill.style.width = '100%';
                
                // 检查登录状态
                await this.checkLoginStatus();
                
                // 关闭模态框
                elements.loginModal.style.display = 'none';
                
                alert('登录流程已启动，请按照浏览器提示完成登录操作。');
            } else {
                utils.showError(data.message || '登录失败');
            }
        } catch (error) {
            console.error('登录失败:', error);
            utils.showError('登录请求失败');
        } finally {
            utils.hideLoading();
        }
    },

    // 初始化登录事件监听
    initLoginEvents() {
        // 登录按钮
        elements.loginBtn.addEventListener('click', () => {
            this.startLogin();
        });

        // 刷新状态按钮
        elements.refreshStatusBtn.addEventListener('click', () => {
            this.checkLoginStatus();
        });

        // 关闭模态框按钮
        elements.closeModalBtn.addEventListener('click', () => {
            elements.loginModal.style.display = 'none';
        });

        // 取消登录按钮
        elements.cancelLoginBtn.addEventListener('click', () => {
            elements.loginModal.style.display = 'none';
        });

        // 确认登录按钮
        elements.confirmLoginBtn.addEventListener('click', () => {
            this.performLogin();
        });

        // 点击模态框外部关闭
        elements.loginModal.addEventListener('click', (e) => {
            if (e.target === elements.loginModal) {
                elements.loginModal.style.display = 'none';
            }
        });
    }
};

// 搜索功能
const searchManager = {
    // 获取选中的平台
    getSelectedPlatforms() {
        const platforms = [];
        document.querySelectorAll('input[name="platform"]:checked').forEach(checkbox => {
            platforms.push(checkbox.value);
        });
        return platforms;
    },

    // 获取排序选项
    getSortOptions() {
        const sortOrder = document.querySelector('input[name="sortOrder"]:checked').value;
        const freeShippingFirst = elements.freeShippingFirst.checked;
        
        return {
            order: sortOrder,
            freeShippingFirst
        };
    },

    // 执行搜索
    async performSearch() {
        const keyword = elements.searchInput.value.trim();
        if (!keyword) {
            alert('请输入搜索关键词');
            return;
        }

        const platforms = this.getSelectedPlatforms();
        if (platforms.length === 0) {
            alert('请至少选择一个搜索平台');
            return;
        }

        const sortOptions = this.getSortOptions();
        appState.currentSearch = keyword;

        try {
            utils.showLoading('正在搜索中，请稍候...');

            const response = await fetch(API_ENDPOINTS.search, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    keyword,
                    platforms,
                    sort: sortOptions
                })
            });

            const data = await response.json();

            if (data.success) {
                appState.searchResults = data.results || [];
                appState.hpoiBestResult = data.hpoiBest || null;
                appState.hpoiRecommendations = data.hpoiRecommendations || [];
                
                this.displayResults();
            } else {
                utils.showError(data.message || '搜索失败');
            }
        } catch (error) {
            console.error('搜索失败:', error);
            utils.showError('搜索请求失败');
        } finally {
            utils.hideLoading();
        }
    },

    // 显示搜索结果
    displayResults() {
        // 更新排序指示器
        const sortOptions = this.getSortOptions();
        const orderText = sortOptions.order === 'desc' ? '降序' : '升序';
        const shippingText = sortOptions.freeShippingFirst ? '，包邮优先' : '';
        elements.sortIndicator.textContent = `按价格${orderText}排列${shippingText}`;

        // 显示结果区域
        elements.resultsSection.style.display = 'block';
        elements.resultsCount.textContent = appState.searchResults.length;

        // 清空现有结果
        elements.resultsContainer.innerHTML = '';

        // 显示结果卡片
        if (appState.searchResults.length === 0) {
            elements.resultsContainer.innerHTML = `
                <div class="no-results">
                    <i class="fas fa-search"></i>
                    <h3>未找到匹配的商品</h3>
                    <p>请尝试其他关键词或调整搜索设置</p>
                </div>
            `;
            return;
        }

        // 渲染结果卡片
        appState.searchResults.forEach(result => {
            const card = this.createResultCard(result);
            elements.resultsContainer.appendChild(card);
        });

        // 显示HPOI最佳商品
        this.displayHpoiBest();

        // 显示HPOI推荐商品
        this.displayHpoiRecommendations();
    },

    // 创建结果卡片
    createResultCard(result) {
        const card = document.createElement('div');
        card.className = 'result-card';
        
        const highlightedTitle = utils.highlightSearchText(result.title, appState.currentSearch);
        const priceText = utils.formatPrice(result.price);
        const shippingText = result.is_free_shipping ? '包邮' : `运费: ¥${result.shipping_fee}`;
        const platformClass = utils.getPlatformColorClass(result.platform);
        const platformIcon = utils.getPlatformIcon(result.platform);
        const platformName = utils.getPlatformName(result.platform);
        
        card.innerHTML = `
            <img src="${result.image_url || 'https://via.placeholder.com/300x200?text=无图片'}" 
                 alt="${result.title}" 
                 class="result-image"
                 onerror="this.src='https://via.placeholder.com/300x200?text=图片加载失败'">
            <div class="result-content">
                <div class="result-title">${highlightedTitle}</div>
                <div class="result-price">${priceText}</div>
                <div class="result-shipping ${result.is_free_shipping ? 'free' : ''}">${shippingText}</div>
                <div class="result-meta">
                    <div class="result-platform ${platformClass}">
                        <i class="${platformIcon}"></i>
                        ${platformName}
                    </div>
                    <div class="result-shop">${result.shop_name || '未知商家'}</div>
                </div>
            </div>
        `;
        
        // 添加点击事件
        card.addEventListener('click', () => {
            if (result.detail_url) {
                window.open(result.detail_url, '_blank');
            }
        });
        
        return card;
    },

    // 显示HPOI最佳商品
    displayHpoiBest() {
        if (!appState.hpoiBestResult) {
            elements.hpoiBestSection.style.display = 'none';
            return;
        }

        elements.hpoiBestSection.style.display = 'block';
        
        const result = appState.hpoiBestResult;
        const priceText = utils.formatPrice(result.price);
        const highlightedTitle = utils.highlightSearchText(result.title, appState.currentSearch);
        
        elements.hpoiBestCard.innerHTML = `
            <div class="hpoi-best-header">
                <h3><i class="fas fa-crown"></i> 最佳推荐</h3>
                <span class="price-badge">最佳匹配</span>
            </div>
            <div class="hpoi-best-content">
                <div class="hpoi-best-title">${highlightedTitle}</div>
                <div class="hpoi-best-details">
                    <div class="hpoi-best-price">售价: ${priceText}</div>
                    <div class="hpoi-best-date">发售日期: ${result.release_date || '未知'}</div>
                </div>
                <div class="hpoi-best-platform">
                    <i class="fas fa-star"></i> HPOI
                </div>
            </div>
        `;
    },

    // 显示HPOI推荐商品
    displayHpoiRecommendations() {
        if (!appState.hpoiRecommendations || appState.hpoiRecommendations.length === 0) {
            elements.hpoiRecommendationsSection.style.display = 'none';
            return;
        }

        elements.hpoiRecommendationsSection.style.display = 'block';
        elements.recommendationsContainer.innerHTML = '';

        appState.hpoiRecommendations.forEach((item, index) => {
            const card = this.createRecommendationCard(item, index);
            elements.recommendationsContainer.appendChild(card);
        });
    },

    // 创建推荐卡片
    createRecommendationCard(item, index) {
        const card = document.createElement('div');
        card.className = 'recommendation-card';
        
        const highlightedTitle = utils.highlightSearchText(item.title, appState.currentSearch);
        const priceText = utils.formatPrice(item.price);
        
        card.innerHTML = `
            <img src="${item.image_url || 'https://via.placeholder.com/250x150?text=无图片'}" 
                 alt="${item.title}" 
                 class="recommendation-image"
                 onerror="this.src='https://via.placeholder.com/250x150?text=图片加载失败'">
            <div class="recommendation-content">
                <div class="recommendation-title">${highlightedTitle}</div>
                <div class="recommendation-price">${priceText}</div>
            </div>
        `;
        
        // 添加点击事件 - 点击后填入搜索框并高亮
        card.addEventListener('click', () => {
            elements.searchInput.value = item.title;
            elements.searchInput.focus();
            elements.searchInput.select();
            
            // 触发搜索
            searchManager.performSearch();
        });
        
        return card;
    },

    // 初始化搜索事件监听
    initSearchEvents() {
        // 搜索按钮
        elements.searchBtn.addEventListener('click', () => {
            this.performSearch();
        });

        // 回车键搜索
        elements.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.performSearch();
            }
        });

        // 排序选项变化时重新显示结果
        document.querySelectorAll('input[name="sortOrder"], #freeShippingFirst').forEach(input => {
            input.addEventListener('change', () => {
                if (appState.searchResults.length > 0) {
                    this.displayResults();
                }
            });
        });
    }
};

// 应用初始化
const app = {
    // 初始化应用
    async init() {
        // 初始化事件监听
        loginManager.initLoginEvents();
        searchManager.initSearchEvents();

        // 初始检查登录状态
        await loginManager.checkLoginStatus();

        // 初始显示示例
        this.showExampleData();
    },

    // 显示示例数据（用于演示）
    showExampleData() {
        // 这里可以添加示例数据，让界面看起来更完整
        // 在实际应用中，这个函数可以移除或用于演示目的
    }
};

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    app.init();
});

// 导出到全局作用域（用于调试）
window.appState = appState;
window.utils = utils;
window.loginManager = loginManager;
window.searchManager = searchManager;