<template>
  <v-snackbar
    v-model="visible"
    :color="color"
    :timeout="timeout"
    location="top right"
    :multi-line="multiline"
  >
    <div class="d-flex align-center">
      <v-icon class="mr-2">{{ icon }}</v-icon>
      <span>{{ message }}</span>
    </div>
    <template v-slot:actions>
      <v-btn
        variant="text"
        @click="visible = false"
      >
        Close
      </v-btn>
    </template>
  </v-snackbar>
</template>

<script>
export default {
  name: 'ErrorSnackbar',
  props: {
    modelValue: {
      type: Boolean,
      default: false
    },
    message: {
      type: String,
      required: true
    },
    type: {
      type: String,
      default: 'error',
      validator: (value) => ['error', 'success', 'warning', 'info'].includes(value)
    },
    timeout: {
      type: Number,
      default: 5000
    },
    multiline: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:modelValue'],
  computed: {
    visible: {
      get() {
        return this.modelValue
      },
      set(value) {
        this.$emit('update:modelValue', value)
      }
    },
    color() {
      const colors = {
        error: 'error',
        success: 'success',
        warning: 'warning',
        info: 'info'
      }
      return colors[this.type] || 'error'
    },
    icon() {
      const icons = {
        error: 'mdi-alert-circle',
        success: 'mdi-check-circle',
        warning: 'mdi-alert',
        info: 'mdi-information'
      }
      return icons[this.type] || 'mdi-alert-circle'
    }
  }
}
</script>

