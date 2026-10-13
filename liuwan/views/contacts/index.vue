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
        <el-table-column prop="phone" label="联系电话" min-width="140" />
        <el-table-column prop="email" label="邮箱" min-width="210" />
      </el-table>
      <el-empty v-else description="没有找到符合条件的联系人" :image-size="100" />

      <p class="directory__note">联系方式为演示数据，请以实际部门信息为准。</p>
    </section>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { OfficeBuilding, Search, User } from '@element-plus/icons-vue'
import { DIRECTORY_CONTACTS } from '@/mock'

const contacts = DIRECTORY_CONTACTS
const keyword = ref('')
const selectedDepartment = ref('')

const departments = computed(() => [...new Set(contacts.map((contact) => contact.department))])

const departmentCounts = computed(() =>
  Object.fromEntries(
    departments.value.map((department) => [
      department,
      contacts.filter((contact) => contact.department === department).length,
    ]),
  ),
)

const filteredContacts = computed(() => {
  const query = keyword.value.trim().toLocaleLowerCase()
  return contacts.filter((contact) => {
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
  gap: var(--st-gap-base);
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.page-description {
  margin: 12px 0 0;
  color: var(--st-text-secondary);
}

.overview {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--st-gap-base);
}

.overview-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  background: var(--st-bg-card);
  border-radius: var(--st-radius-base);
  box-shadow: var(--st-shadow-card);
}

.overview-card__icon {
  display: grid;
  width: 44px;
  height: 44px;
  color: var(--st-primary);
  font-size: 20px;
  background: var(--st-primary-light);
  border-radius: var(--st-radius-base);
  place-items: center;
}

.overview-card__icon--department {
  color: var(--st-success);
  background: var(--st-success-light);
}

.overview-card__value {
  font-size: 22px;
  font-weight: 700;
}

.overview-card__label {
  margin-top: 3px;
  color: var(--st-text-secondary);
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
  font-size: 16px;
}

.directory__head p {
  margin: 7px 0 0;
  color: var(--st-text-secondary);
  font-size: 13px;
}

.directory__count {
  flex-shrink: 0;
  color: var(--st-text-secondary);
}

.filters {
  display: flex;
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

.department-chip {
  padding: 7px 12px;
  color: var(--st-text-regular);
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
  margin-left: 4px;
  color: var(--st-text-secondary);
}

.department-chip:hover,
.department-chip--active {
  color: var(--st-primary);
  background: var(--st-primary-light);
  border-color: var(--st-primary-glow);
}

.contact-name {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
}

.contact-name__avatar {
  color: var(--st-primary-dark);
  background: var(--st-primary-light);
}

.directory__note {
  margin: var(--st-gap-base) 0 0;
  color: var(--st-text-secondary);
  font-size: 12px;
}

@media (max-width: 640px) {
  .overview {
    gap: var(--st-gap-sm);
  }

  .overview-card {
    gap: var(--st-gap-sm);
    padding: 14px 12px;
  }

  .overview-card__icon {
    width: 38px;
    height: 38px;
  }

  .directory {
    padding: var(--st-gap-base);
  }

  .directory__head {
    flex-direction: column;
  }

  .filters {
    flex-direction: column;
  }

  .filters__search,
  .filters__department {
    width: 100%;
    max-width: none;
  }
}
</style>
