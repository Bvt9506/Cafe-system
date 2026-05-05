<template>
  <div class="layout-container">
    <header class="pos-header">
      <div class="left-head">
        <button class="btn-back" @click="goBack">← Trở lại</button>
        <span class="title">Bàn {{ orderStore.currentTable }} (HD: {{ orderStore.currentOrderId }})</span>
      </div>
    </header>

    <div class="main-content">
      <!-- MÀN HÌNH CHỌN MÓN (TRÁI) -->
      <div class="menu-area">
        <div class="category-tabs">
          <button 
            v-for="cat in categories" 
            :key="cat"
            :class="['tab-btn', currentCategory === cat ? 'active' : '']"
            @click="currentCategory = cat"
          >
            {{ cat }}
          </button>
        </div>

        <div class="menu-grid">
          <div 
            v-for="mon in filteredMenu" 
            :key="mon.ma_mon"
            class="menu-item"
            @click="openItemModal(mon)"
          >
            <div class="item-img-placeholder">
              <span v-if="!mon.hinh_anh">☕</span>
              <img v-else :src="mon.hinh_anh" alt="" class="item-img" />
            </div>
            <div class="item-info">
              <div class="item-name">{{ mon.ten_mon }}</div>
              <div class="item-price">{{ formatPrice(mon.don_gia) }}đ</div>
            </div>
          </div>
        </div>
      </div>

      <!-- HÓA ĐƠN ĐANG CHỌN (PHẢI) -->
      <div class="order-area">
        <h3>Hóa đơn tạm tính</h3>
        <div class="order-list">
          <div v-if="!orderStore.orderItems.length" class="empty-msg">Chưa có món nào.</div>
          <div v-for="item in orderStore.orderItems" :key="item.id" class="order-row">
            <div class="row-main">
              <span class="row-name">
                {{ item.ten_mon }}
                <small v-if="item.ghi_chu" class="item-note"><br/>* {{ item.ghi_chu }}</small>
              </span>
              <span class="row-qty">x{{ item.so_luong }}</span>
              <span class="row-price">{{ formatPrice(item.thanh_tien) }}đ</span>
            </div>
            <div class="row-actions">
              <button class="btn-icon" @click="openEditModal(item)">✏️</button>
              <button class="btn-icon" @click="removeItem(item.id)">🗑️</button>
            </div>
          </div>
        </div>

        <div class="order-summary">
          <div class="total-line">
            <span>Tổng cộng:</span>
            <span class="total-price">{{ formatPrice(subtotal) }}đ</span>
          </div>
          <button class="btn-checkout" :disabled="!orderStore.orderItems.length" @click="goToCheckout">
            THANH TOÁN
          </button>
        </div>
      </div>
    </div>

    <!-- MODAL CUSTOMIZE MÓN -->
    <div v-if="showItemModal" class="modal-overlay" @click.self="showItemModal = false">
      <div class="modal-content">
        <h3>{{ selectedMon?.ten_mon }}</h3>
        <p class="modal-price">{{ formatPrice(selectedMon?.don_gia) }}đ</p>
        
        <div class="form-group">
          <label>Số lượng</label>
          <div class="qty-control">
            <button type="button" @click="decreaseQuantity">-</button>
            <input type="number" v-model.number="itemQuantity" min="1" />
            <button type="button" @click="increaseQuantity">+</button>
          </div>
        </div>

        <div class="form-group">
          <label>Ghi chú (Tùy chọn)</label>
          <input type="text" v-model="itemNote" placeholder="VD: Ít đá, nhiều đường..." class="note-input" />
        </div>

        <div class="modal-actions">
          <button class="btn-cancel" @click="showItemModal = false">Hủy</button>
          <button class="btn-confirm" @click="confirmAddItem">Thêm vào đơn ({{ formatPrice((selectedMon?.don_gia || 0) * itemQuantity) }}đ)</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/axios';
import { useOrderStore } from '../stores/order';

const router = useRouter();
const orderStore = useOrderStore();

const menu = ref([]);
const categories = ref(['Tất cả']);
const currentCategory = ref('Tất cả');

// Variables for customization modal
const showItemModal = ref(false);
const selectedMon = ref(null);
const itemQuantity = ref(1);
const itemNote = ref('');
const editingItemId = ref(null);

const fetchMenu = async () => {
  try {
    const res = await api.get('/api/menu/');
    if (res.data.success) {
      menu.value = res.data.data;
      const cats = new Set(menu.value.map(m => m.ma_loai));
      categories.value = ['Tất cả', ...Array.from(cats)];
    }
  } catch (err) {
    console.error(err);
  }
};

// Cập nhật chi tiết HĐ từ server
const refreshOrder = async () => {
  try {
    const res = await api.get(`/api/orders/${orderStore.currentOrderId}/`);
    if (res.data.success) {
      orderStore.orderItems = res.data.data.chi_tiet;
      orderStore.currentCustomerTier = res.data.data.hang_khach_hang;
    }
  } catch (err) {
    console.error(err);
  }
};

onMounted(() => {
  if (!orderStore.currentOrderId) {
    router.push('/tables');
    return;
  }
  fetchMenu();
  refreshOrder();
});

const filteredMenu = computed(() => {
  if (currentCategory.value === 'Tất cả') return menu.value;
  return menu.value.filter(m => m.ma_loai === currentCategory.value);
});

const subtotal = computed(() => {
  return orderStore.orderItems.reduce((acc, curr) => acc + parseFloat(curr.thanh_tien), 0);
});

const decreaseQuantity = () => {
  if (itemQuantity.value > 1) itemQuantity.value--;
};

const increaseQuantity = () => {
  itemQuantity.value++;
};

const openItemModal = (mon) => {
  editingItemId.value = null;
  selectedMon.value = mon;
  itemQuantity.value = 1;
  itemNote.value = '';
  showItemModal.value = true;
};

const openEditModal = (item) => {
  editingItemId.value = item.id;
  selectedMon.value = {
    ma_mon: item.ma_mon,
    ten_mon: item.ten_mon,
    don_gia: item.gia_ban
  };
  itemQuantity.value = item.so_luong;
  itemNote.value = item.ghi_chu || '';
  showItemModal.value = true;
};

const confirmAddItem = async () => {
  try {
    if (editingItemId.value) {
      await api.patch(`/api/orders/${orderStore.currentOrderId}/items/${editingItemId.value}/`, {
        so_luong: itemQuantity.value,
        ghi_chu: itemNote.value
      });
    } else {
      await api.post(`/api/orders/${orderStore.currentOrderId}/items/`, {
        ma_mon: selectedMon.value.ma_mon,
        so_luong: itemQuantity.value,
        ghi_chu: itemNote.value
      });
    }
    refreshOrder();
    showItemModal.value = false;
  } catch (err) {
    alert("Lỗi thêm/sửa món: " + (err.response?.data?.message || err.message));
  }
};

const removeItem = async (itemId) => {
  try {
    await api.delete(`/api/orders/${orderStore.currentOrderId}/items/${itemId}/`);
    refreshOrder();
  } catch (err) {
    alert("Lỗi xóa món.");
  }
};

const goToCheckout = () => {
  router.push('/checkout');
};

const goBack = () => {
  router.push('/tables');
};

const formatPrice = (price) => {
  return Number(price).toLocaleString('vi-VN');
};
</script>

<style scoped>
.layout-container {
  display: flex;
  flex-direction: column;
  height: 100vh;
}
.pos-header {
  background-color: #2c3e50;
  color: white;
  padding: 15px 20px;
}
.left-head { display: flex; align-items: center; }
.btn-back { margin-right: 20px; padding: 8px 12px; background: rgba(255,255,255,0.2); color: white;}
.title { font-size: 20px; font-weight: bold; }

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

/* MENU AREA */
.menu-area {
  flex: 2;
  background-color: #f4f7f6;
  padding: 20px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.category-tabs {
  display: flex;
  overflow-x: auto;
  margin-bottom: 20px;
  gap: 10px;
}
.tab-btn {
  padding: 10px 20px;
  background: white;
  border: 1px solid #ddd;
  white-space: nowrap;
}
.tab-btn.active {
  background: #2980b9;
  color: white;
  border-color: #2980b9;
}
.menu-grid {
  flex: 1;
  overflow-y: auto;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 15px;
  align-content: start;
}
.menu-item {
  background: white;
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 0 2px 5px rgba(0,0,0,0.05);
  cursor: pointer;
  transition: transform 0.1s;
}
.menu-item:hover { transform: translateY(-3px); }
.item-img-placeholder {
  height: 120px;
  background: #ecf0f1;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 40px;
}
.item-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.item-info {
  padding: 12px;
}
.item-name { font-weight: 600; margin-bottom: 5px; }
.item-price { color: #e67e22; font-weight: bold; }

/* ORDER AREA */
.order-area {
  flex: 1;
  background-color: white;
  border-left: 1px solid #ddd;
  display: flex;
  flex-direction: column;
}
.order-area h3 {
  padding: 20px;
  margin: 0;
  border-bottom: 1px solid #eee;
  background: #fafafa;
}
.order-list {
  flex: 1;
  overflow-y: auto;
  padding: 10px 20px;
}
.empty-msg { color: #999; text-align: center; margin-top: 50px; }
.order-row {
  border-bottom: 1px dashed #ddd;
  padding: 15px 0;
}
.row-main {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 16px;
}
.row-name { flex: 2; font-weight: 500;}
.row-qty { flex: 1; text-align: center; color: #7f8c8d;}
.row-price { flex: 1; text-align: right; font-weight: bold;}
.btn-icon { background: none; color: #e74c3c; padding: 5px;}

.order-summary {
  padding: 20px;
  border-top: 2px solid #eee;
  background: #fafafa;
}
.total-line {
  display: flex;
  justify-content: space-between;
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 20px;
}
.total-price { color: #c0392b; }
.btn-checkout {
  width: 100%;
  padding: 18px;
  background-color: #27ae60;
  color: white;
  font-size: 18px;
}
.btn-checkout:disabled { background-color: #95a5a6; cursor: not-allowed; }

/* MODAL STYLES */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}
.modal-content {
  background: white;
  padding: 25px;
  border-radius: 12px;
  width: 400px;
  max-width: 90%;
}
.modal-content h3 { margin-top: 0; margin-bottom: 5px; }
.modal-price { color: #e67e22; font-weight: bold; margin-bottom: 20px; font-size: 18px;}
.form-group { margin-bottom: 15px; }
.form-group label { display: block; margin-bottom: 8px; font-weight: 500; }
.qty-control { display: flex; align-items: center; }
.qty-control button { width: 40px; height: 40px; font-size: 20px; background: #ecf0f1; border: none; cursor: pointer; border-radius: 4px;}
.qty-control input { width: 60px; height: 40px; text-align: center; font-size: 16px; margin: 0 10px; border: 1px solid #ddd; border-radius: 4px;}
.note-input { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box;}
.modal-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 25px; }
.btn-cancel { padding: 10px 15px; background: #ecf0f1; border: none; border-radius: 4px; cursor: pointer; }
.btn-confirm { padding: 10px 15px; background: #27ae60; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;}
.item-note { color: #7f8c8d; font-size: 13px; font-style: italic; }
</style>
