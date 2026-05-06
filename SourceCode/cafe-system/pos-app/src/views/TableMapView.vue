<template>
  <div class="layout-container">
    <header class="pos-header">
      <div class="logo">Cafe POS</div>
      <div class="actions">
        <button class="btn-warning" @click="handleCheckoutShift">Kết thúc ca</button>
        <button class="btn-danger" @click="handleLogout">Đăng xuất</button>
      </div>
    </header>

    <div class="main-content">
      <div class="sidebar">
        <h3>Ghi chú bàn</h3>
        <ul class="legend">
          <li><span class="color-box empty"></span> Trống ({{ emptyTablesCount }})</li>
          <li><span class="color-box occupied"></span> Có khách ({{ occupiedTablesCount }})</li>
        </ul>
        <div class="table-actions">
          <button class="btn-info" :class="{ 'btn-active-mode': isTransferMode }" @click="toggleTransferMode">
            {{ isTransferMode ? 'Hủy chuyển bàn' : 'Chuyển bàn' }}
          </button>
          <button class="btn-info" :class="{ 'btn-active-mode': isMergeMode }" @click="toggleMergeMode">
            {{ isMergeMode ? 'Hủy gộp bàn' : 'Gộp bàn' }}
          </button>
        </div>

        <!-- Merge mode info panel -->
        <div v-if="isMergeMode" class="merge-panel">
          <div v-if="mergeSource">
            <p class="merge-label">Bàn chính: <strong>Bàn {{ mergeSource.ma_ban }}</strong></p>
            <p v-if="mergeTargets.length > 0" class="merge-label">
              Sẽ gộp vào Bàn {{ mergeSource.ma_ban }}:
              <strong>{{ mergeTargets.map(b => 'Bàn ' + b.ma_ban).join(', ') }}</strong>
            </p>
            <button
              v-if="mergeTargets.length > 0"
              class="btn-confirm-merge"
              @click="confirmMerge"
            >Xác nhận gộp</button>
          </div>
        </div>
      </div>

      <div class="map-area">
        <h2 style="margin-top: 0;">Sơ đồ Bàn</h2>

        <div v-if="isTransferMode" class="transfer-banner">
          {{ transferSource ? 'Chọn bàn muốn chuyển đến (bàn trống)' : 'Chọn bàn muốn chuyển đi (bàn đang có khách)' }}
        </div>
        <div v-if="isMergeMode" class="merge-banner">
          {{ mergeSource ? `Chọn các bàn muốn gộp vào Bàn ${mergeSource.ma_ban}, sau đó nhấn Xác nhận gộp` : 'Chọn bàn chính (bàn giữ hóa đơn)' }}
        </div>

        <div v-if="loading" class="loading">Đang tải sơ đồ...</div>
        
        <div v-else class="table-grid">
          <div 
            v-for="ban in tables" 
            :key="ban.ma_ban"
            class="table-card"
            :class="[
              getStatusClass(ban.trang_thai),
              isTransferMode && transferSource?.ma_ban === ban.ma_ban ? 'table-selected-transfer' : '',
              isMergeMode && mergeSource?.ma_ban === ban.ma_ban ? 'table-selected-transfer' : '',
              isMergeMode && mergeTargets.some(b => b.ma_ban === ban.ma_ban) ? 'table-selected-merge-phu' : ''
            ]"
            @click="handleTableClick(ban)"
          >
            <div class="table-name">Bàn {{ ban.ma_ban }}</div>
            <div class="table-zone">{{ ban.ten_khu_vuc }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- TABLE ACTION MODAL -->
    <div v-if="showTableModal" class="modal-overlay" @click.self="showTableModal = false">
      <div class="modal-content">
        <h3>Bàn {{ selectedTable?.ma_ban }} - {{ selectedTable?.ten_khu_vuc }}</h3>
        
        <div class="action-group">
          <h4>Thao tác Hóa đơn</h4>
          <button v-if="Number(selectedTable?.trang_thai) === 0" class="btn-primary w-100" @click="handleCreateOrder(selectedTable)">
            Tạo hóa đơn mới
          </button>
          <button v-else-if="Number(selectedTable?.trang_thai) === 1" class="btn-primary w-100" @click="handleViewOrder(selectedTable)">
            Xem hóa đơn
          </button>
        </div>

        <div class="action-group">
          <h4>Cập nhật trạng thái</h4>
          <div class="status-buttons">
            <button 
              :class="['btn-status', Number(selectedTable?.trang_thai) === 0 ? 'active-empty' : '']" 
              @click="changeTableStatus(selectedTable, 0)">Trống
            </button>
            <button 
              :class="['btn-status', Number(selectedTable?.trang_thai) === 1 ? 'active-occupied' : '']" 
              @click="changeTableStatus(selectedTable, 1)">Có khách
            </button>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn-cancel" @click="showTableModal = false">Đóng</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import api from '../services/axios';
import { useAuthStore } from '../stores/auth';
import { useOrderStore } from '../stores/order';

const router = useRouter();
const authStore = useAuthStore();
const orderStore = useOrderStore();

const tables = ref([]);
const loading = ref(true);

const emptyTablesCount = computed(() => tables.value.filter(t => Number(t.trang_thai) === 0).length);
const occupiedTablesCount = computed(() => tables.value.filter(t => Number(t.trang_thai) === 1).length);

// Transfer state
const isTransferMode = ref(false);
const transferSource = ref(null);

// Merge state
const isMergeMode = ref(false);
const mergeSource = ref(null);
const mergeTargets = ref([]);

const showTableModal = ref(false);
const selectedTable = ref(null);

const fetchTables = async () => {
  loading.value = true;
  try {
    const res = await api.get('/api/tables/');
    if (res.data.success) {
      tables.value = res.data.data;
    }
  } catch (err) {
    console.error("Failed to load tables", err);
  } finally {
    loading.value = false;
  }
};

onMounted(() => {
  fetchTables();
});

const getStatusClass = (status) => {
  const s = Number(status);
  if (s === 0) return 'status-empty';
  if (s === 1) return 'status-occupied';
  return 'status-empty';
};

const toggleTransferMode = () => {
  isTransferMode.value = !isTransferMode.value;
  transferSource.value = null;
  // Tắt merge mode nếu đang bật
  if (isTransferMode.value) {
    isMergeMode.value = false;
    mergeSource.value = null;
    mergeTargets.value = [];
  }
};

const toggleMergeMode = () => {
  isMergeMode.value = !isMergeMode.value;
  mergeSource.value = null;
  mergeTargets.value = [];
  // Tắt transfer mode nếu đang bật
  if (isMergeMode.value) {
    isTransferMode.value = false;
    transferSource.value = null;
  }
};

const confirmMerge = async () => {
  if (!mergeSource.value || mergeTargets.value.length === 0) return;
  try {
    const res = await api.post('/api/tables/merge/', {
      ban_chinh: mergeSource.value.ma_ban,
      ban_phu: mergeTargets.value.map(b => b.ma_ban)
    });
    if (res.data.success) {
      alert('Gộp bàn thành công');
      isMergeMode.value = false;
      mergeSource.value = null;
      mergeTargets.value = [];
      fetchTables();
    }
  } catch (err) {
    alert('Gộp bàn thất bại: ' + (err.response?.data?.message || err.message));
  }
};

const handleTableClick = async (ban) => {
  // --- Chế độ Chuyển bàn ---
  if (isTransferMode.value) {
    if (!transferSource.value) {
      if (Number(ban.trang_thai) === 1) {
        transferSource.value = ban;
      }
    } else {
      if (Number(ban.trang_thai) === 0) {
        try {
          const res = await api.post('/api/tables/transfer/', {
            tu_ban: transferSource.value.ma_ban,
            den_ban: ban.ma_ban
          });
          if (res.data.success) {
            alert('Chuyển bàn thành công');
            isTransferMode.value = false;
            transferSource.value = null;
            fetchTables();
          }
        } catch (err) {
          alert('Chuyển bàn thất bại: ' + (err.response?.data?.message || err.message));
        }
      }
    }
    return;
  }

  // --- Chế độ Gộp bàn ---
  if (isMergeMode.value) {
    if (Number(ban.trang_thai) !== 1) return; // Chỉ cho chọn bàn đỏ

    if (!mergeSource.value) {
      // Bước 2: Chọn bàn chính
      mergeSource.value = ban;
    } else if (ban.ma_ban === mergeSource.value.ma_ban) {
      // Click lại bàn chính → bỏ chọn tất cả
      mergeSource.value = null;
      mergeTargets.value = [];
    } else {
      // Bước 3: Toggle bàn phụ
      const idx = mergeTargets.value.findIndex(b => b.ma_ban === ban.ma_ban);
      if (idx >= 0) {
        mergeTargets.value.splice(idx, 1); // Bỏ chọn
      } else {
        mergeTargets.value.push(ban); // Thêm chọn
      }
    }
    return;
  }

  // --- Bình thường: mở modal ---
  selectedTable.value = ban;
  showTableModal.value = true;
};

const handleCreateOrder = async (ban) => {
  try {
    const res = await api.post('/api/orders/', { ma_ban: ban.ma_ban });
    if (res.data.success) {
      orderStore.setOrder(ban.ma_ban, res.data.data.ma_hd, [], res.data.data.hang_khach_hang);
      router.push('/order');
    }
  } catch (err) {
    alert(err.response?.data?.message || "Lỗi tạo hóa đơn");
  }
};

const handleViewOrder = async (ban) => {
  try {
    const res = await api.get(`/api/orders/?ban=${ban.ma_ban}&trang_thai=Chờ pha chế`);
    if (res.data.success && res.data.data.length > 0) {
      const order = res.data.data[0];
      orderStore.setOrder(ban.ma_ban, order.ma_hd, order.chi_tiet, order.hang_khach_hang);
      router.push('/order');
    } else {
      alert("Không tìm thấy hóa đơn mở cho bàn này!");
    }
  } catch (err) {
    console.error(err);
  }
};

const changeTableStatus = async (ban, newStatus) => {
  if (ban.trang_thai === newStatus) return;
  try {
    const res = await api.patch(`/api/tables/${ban.ma_ban}/status/`, { trang_thai: newStatus });
    if (res.data.success) {
      ban.trang_thai = newStatus;
      showTableModal.value = false;
      fetchTables();
    }
  } catch (err) {
    alert(err.response?.data?.message || "Lỗi cập nhật trạng thái bàn");
  }
};

const handleCheckoutShift = () => {
  router.push('/checkout-shift');
};

const handleLogout = () => {
  authStore.logout();
  router.push('/login');
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
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.logo {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: 1px;
}
.actions button {
  padding: 8px 16px;
  margin-left: 10px;
}
.btn-warning { background-color: #f39c12; color: white; }
.btn-danger { background-color: #e74c3c; color: white; }
.btn-info { background-color: #3498db; color: white; width: 100%; padding: 12px; margin-bottom: 10px;}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}
.sidebar {
  width: 250px;
  background-color: white;
  border-right: 1px solid #ddd;
  padding: 20px;
  display: flex;
  flex-direction: column;
}
.legend {
  list-style: none;
  padding: 0;
  margin-bottom: 40px;
}
.legend li {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  font-size: 16px;
}
.color-box {
  width: 20px;
  height: 20px;
  border-radius: 4px;
  margin-right: 10px;
}
.empty { background-color: #2ecc71; }
.occupied { background-color: #e74c3c; }
.cleaning { background-color: #f1c40f; }

.map-area {
  flex: 1;
  padding: 20px;
  background-color: #ecf0f1;
  overflow-y: auto;
}
.table-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
}
.table-card {
  height: 120px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  cursor: pointer;
  color: white;
  background-color: #2ecc71;
  box-shadow: 0 4px 6px rgba(0,0,0,0.1);
  transition: transform 0.1s;
}
.table-card:hover {
  transform: scale(1.05);
}
.table-card .table-name {
  font-size: 20px;
  font-weight: bold;
}
.table-card .table-zone {
  font-size: 14px;
  opacity: 0.8;
  margin-top: 5px;
}

.status-empty { background-color: #2ecc71; }
.status-occupied { background-color: #e74c3c; }
.status-cleaning { background-color: #f1c40f; color: #333; }

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
.modal-content h3 { margin-top: 0; margin-bottom: 20px; font-size: 22px; color: #2c3e50; }
.action-group { margin-bottom: 25px; }
.action-group h4 { margin-top: 0; margin-bottom: 10px; color: #7f8c8d; font-size: 14px; text-transform: uppercase; }
.btn-primary { background-color: #3498db; color: white; border: none; padding: 12px; border-radius: 6px; font-size: 16px; cursor: pointer; font-weight: bold; }
.w-100 { width: 100%; }
.warning-text { color: #f39c12; font-style: italic; margin: 0; }
.status-buttons { display: flex; gap: 10px; }
.btn-status { flex: 1; padding: 10px; border: 1px solid #ddd; background: white; border-radius: 6px; cursor: pointer; font-weight: 500; transition: all 0.2s;}
.btn-status:hover { background: #f9f9f9; }
.active-empty { background-color: #2ecc71 !important; color: white; border-color: #2ecc71; }
.active-occupied { background-color: #e74c3c !important; color: white; border-color: #e74c3c; }
.active-cleaning { background-color: #f1c40f !important; color: #333; border-color: #f1c40f; }
.modal-actions { display: flex; justify-content: flex-end; margin-top: 15px; }
.btn-cancel { padding: 10px 20px; background: #ecf0f1; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; color: #7f8c8d; }

/* TRANSFER CSS */
.transfer-banner {
  background-color: #34495e;
  color: white;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
  font-weight: bold;
  margin-bottom: 20px;
  font-size: 16px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.table-selected-transfer {
  border: 4px solid #f1c40f !important;
  box-shadow: 0 0 15px rgba(241, 196, 15, 0.6) !important;
  transform: scale(1.05);
}

.table-selected-merge-phu {
  border: 4px solid #3498db !important;
  box-shadow: 0 0 15px rgba(52, 152, 219, 0.6) !important;
  transform: scale(1.05);
}

.merge-banner {
  background-color: #8e44ad;
  color: white;
  padding: 12px;
  border-radius: 8px;
  text-align: center;
  font-weight: bold;
  margin-bottom: 20px;
  font-size: 16px;
  box-shadow: 0 2px 5px rgba(0,0,0,0.1);
}

.btn-active-mode {
  background-color: #c0392b !important;
}

.merge-panel {
  margin-top: 16px;
  background: #f4f4f4;
  border-radius: 8px;
  padding: 12px;
  font-size: 14px;
}

.merge-label {
  margin: 4px 0 8px;
  color: #2c3e50;
}

.btn-confirm-merge {
  width: 100%;
  padding: 10px;
  background-color: #27ae60;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  font-size: 14px;
  cursor: pointer;
  margin-top: 8px;
  transition: background 0.2s;
}

.btn-confirm-merge:hover {
  background-color: #219a52;
}
</style>
