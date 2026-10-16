<template>
  <div class="contacts">
    <div class="page-head">
      <div>
        <h2 class="page-title">通讯录</h2>
        <p class="page-description">查看学生工作小组联系人及所属部门</p>
      </div>
    </div>

    <div class="overview">
      <div class="overview-card">
        <span class="overview-card__icon">
          <el-icon><User /></el-icon>
        </span>
        <div>
          <div class="overview-card__value">{{ contacts.length }}</div>
          <div class="overview-card__label">联系人</div>
        </div>
      </div>
      <div class="overview-card">
        <span class="overview-card__icon overview-card__icon--department">
          <el-icon><OfficeBuilding /></el-icon>
        </span>
        <div>
          <div class="overview-card__value">{{ departments.length }}</div>
          <div class="overview-card__label">部门 / 小组</div>
        </div>
      </div>
    </div>

    <section class="directory page-block">
      <div class="directory__head">
        <div>
          <h3>联系人列表</h3>
          <p>按姓名、部门或岗位搜索，也可以按部门筛选</p>
        </div>
        <span class="directory__count">共 {{ filteredContacts.length }} 位</span>
      </div>

      <div class="filters">
        <el-input
          v-model="keyword"
          clearable
          class="filters__search"
          placeholder="搜索姓名、部门或岗位"
          aria-label="搜索联系人"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-select v-model="selectedDepartment" class="filters__department" aria-label="按部门筛选">
          <el-option label="全部部门" value="" />
          <el-option
            v-for="department in departments"
            :key="department"
            :label="department"
            :value="department"
          />
        </el-select>
      </div>

      <div class="department-list" aria-label="部门分组">
        <button
          type="button"
          :class="['department-chip', { 'department-chip--active': selectedDepartment === '' }]"
          @click="selectedDepartment = ''"
        >
          全部
          <span>{{ contacts.length }}</span>
        </button>
        <button
          v-for="department in departments"
          :key="department"
          type="button"
          :class="[
            'department-chip',
            { 'department-chip--active': selectedDepartment === department },
          ]"
          @click="selectedDepartment = department"
        >
          {{ department }}
          <span>{{ departmentCounts[department] }}</span>
        </button>
      </div>

      <el-table v-if="filteredContacts.length" :data="filteredContacts" row-key="id">
        <el-table-column label="联系人" min-width="180">
          <template #default="{ row }">
            <div class="contact-name">
              <el-avatar :size="38" class="contact-name__avatar">
                {{ row.name.slice(0, 1) }}
              </el-avatar>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="部门 / 小组" min-width="140">
          <template #default="{ row }">
            <el-tag effect="plain" round>{{ row.department }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="role" label="岗位" min-width="150" />
        <el-table-column label="联系电话" min-width="180">
          <template #default="{ row }">
            <div class="phone-cell">
              <span class="phone-mask" v-if="!row.phoneVisible">{{ row.phone }}</span>
              <a v-else :href="`tel:${row.phoneFull}`" class="phone-link">{{ row.phoneFull }}</a>
              <button
                type="button"
                class="phone-toggle"
                @click="togglePhone(row.id)"
                :aria-label="row.phoneVisible ? '隐藏电话' : '查看电话'"
              >
                <el-icon>
                  <View v-if="!row.phoneVisible" />
                  <Hide v-else />
                </el-icon>
                {{ row.phoneVisible ? '隐藏' : '查看' }}
              </button>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="email" label="邮箱" min-width="210" />
      </el-table>
      <el-empty v-else description="没有找到符合条件的联系人" :image-size="100" />

      <p class="directory__note">联系方式为演示数据，请以实际部门信息为准。</p>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { Hide, OfficeBuilding, Search, User, View } from '@element-plus/icons-vue'
import { DIRECTORY_CONTACTS } from '@/mock'

const contacts = ref(
  DIRECTORY_CONTACTS.map((contact) => ({
    ...contact,
    phoneVisible: false,
  })),
)
const keyword = ref('')
const selectedDepartment = ref('')

const departments = computed(() => [
  ...new Set(contacts.value.map((contact) => contact.department)),
])

const departmentCounts = computed(() =>
  Object.fromEntries(
    departments.value.map((department) => [
      department,
      contacts.value.filter((contact) => contact.department === department).length,
    ]),
  ),
)

const togglePhone = (id) => {
  const contact = contacts.value.find((item) => item.id === id)
  if (!contact) return
  contact.phoneVisible = !contact.phoneVisible
}

const filteredContacts = computed(() => {
  const query = keyword.value.trim().toLocaleLowerCase()
  return contacts.value.filter((contact) => {
    const matchesDepartment =
      !selectedDepartment.value || contact.department === selectedDepartment.value
    const searchable = [contact.name, contact.department, contact.role]
      .join(' ')
      .toLocaleLowerCase()
    return matchesDepartment && (!query || searchable.includes(query))
  })
})
</script>

<style scoped>
.contacts {
  display: flex;
  flex-direction: column;
  gap: var(--st-page-gap);
  color: var(--st-text-regular);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.page-description {
  margin: var(--st-gap-md) 0 0;
  color: var(--st-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.overview {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--st-gap-base);
}

.overview-card {
  display: flex;
  align-items: center;
  gap: var(--st-gap-base);
  padding: var(--st-gap-base) var(--st-gap-lg);
  background: var(--st-bg-card);
  border: 1px solid var(--st-border-color-hair);
  border-radius: var(--st-radius-card);
  box-shadow: var(--st-shadow-card);
}

.overview-card__icon {
  display: grid;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  color: var(--st-primary-dark);
  font-size: 20px;
  background: var(--st-primary-light);
  border-radius: var(--st-radius-base);
  place-items: center;
}

/* 第二个图标用本模块（通讯录 = 品红）的浅色做底，只占 44px 小面积。
   v4：从 fade 提到 soft —— 44px 的小方块用 fade 档等于白底，看不出是「本模块色」。 */
.overview-card__icon--department {
  color: var(--module-ink, var(--tone-pink-deep));
  background: var(--tone-pink-soft);
}

.overview-card__value {
  color: var(--st-text-primary);
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.01em;
  font-variant-numeric: tabular-nums;
}

.overview-card__label {
  margin-top: var(--st-gap-xs);
  color: var(--st-text-secondary);
  font-size: 13px;
}

.directory {
  margin-bottom: 0;
}

.directory__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--st-gap-base);
}

.directory__head h3 {
  margin: 0;
  color: var(--st-text-primary);
  font-size: 15px;
  font-weight: 600;
  line-height: 1.5;
  letter-spacing: -0.01em;
}

.directory__head p {
  margin: var(--st-gap-sm) 0 0;
  color: var(--st-text-secondary);
  font-size: 13px;
  line-height: 1.6;
}

.directory__count {
  flex-shrink: 0;
  color: var(--st-text-secondary);
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  gap: var(--st-gap-sm);
  margin: var(--st-gap-lg) 0 var(--st-gap-base);
}

.filters__search {
  max-width: 420px;
}

.filters__department {
  width: 180px;
}

.department-list {
  display: flex;
  flex-wrap: wrap;
  gap: var(--st-gap-sm);
  margin-bottom: var(--st-gap-base);
}

.phone-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 28px;
}

.phone-mask,
.phone-link {
  font-variant-numeric: tabular-nums;
  letter-spacing: 0.02em;
}

.phone-link {
  color: var(--st-primary);
  text-decoration: none;
}

.phone-toggle {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  color: var(--st-text-secondary);
  cursor: pointer;
  background: transparent;
  border: 1px solid var(--st-border-color);
  border-radius: 999px;
}

.phone-toggle:hover {
  color: var(--st-primary);
  border-color: var(--st-primary-light);
}

.department-chip {
  display: inline-flex;
  align-items: center;
  gap: var(--st-gap-xs);
  min-height: 32px;
  padding: var(--st-gap-xs) var(--st-gap-md);
  color: var(--st-text-regular);
  font-size: 13px;
  cursor: pointer;
  background: var(--st-bg-page);
  border: 1px solid transparent;
  border-radius: var(--st-radius-pill);
  transition:
    color var(--st-duration-fast) var(--st-ease),
    background-color var(--st-duration-fast) var(--st-ease),
    border-color var(--st-duration-fast) var(--st-ease);
}

.department-chip span {
  color: var(--st-text-secondary);
  font-variant-numeric: tabular-nums;
}

.department-chip:hover {
  color: var(--st-primary);
  background: var(--st-primary-lighter);
  border-color: var(--st-border-color);
}

.department-chip--active {
  color: var(--st-primary);
  background: var(--st-primary-light);
  border-color: var(--st-primary-glow);
}

.department-chip:focus-visible {
  outline: 2px solid var(--st-primary);
  outline-offset: 2px;
}

.contact-name {
  display: flex;
  align-items: center;
  gap: var(--st-gap-md);
  color: var(--st-text-primary);
  font-weight: 600;
}

/* 字母头像：品牌浅底 + 品牌蓝字 */
.contact-name__avatar {
  color: var(--st-primary);
  font-size: 15px;
  font-weight: 600;
  background: var(--st-primary-light);
}

.directory__note {
  margin: var(--st-gap-base) 0 0;
  color: var(--st-text-secondary);
  font-size: 12px;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .page-description {
    margin-top: var(--st-gap-sm);
  }

  .overview {
    gap: var(--st-gap-sm);
  }

  .overview-card {
    gap: var(--st-gap-md);
    padding: var(--st-gap-base);
  }

  .overview-card__icon {
    width: 38px;
    height: 38px;
    font-size: 18px;
  }

  .overview-card__value {
    font-size: 20px;
  }

  .directory {
    padding: var(--st-gap-base);
  }

  .directory__head {
    flex-direction: column;
    gap: var(--st-gap-xs);
  }

  .filters {
    flex-direction: column;
  }

  .filters__search,
  .filters__department {
    width: 100%;
    max-width: none;
  }

  /* 手指点得准：筛选按钮给足触摸目标 */
  .department-chip {
    min-height: 44px;
    padding: var(--st-gap-sm) var(--st-gap-base);
  }
}
</style>
