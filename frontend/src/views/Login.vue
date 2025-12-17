<template>
  <v-app>
    <v-main>
      <v-container fluid fill-height>
        <v-row align="center" justify="center">
          <v-col cols="12" sm="8" md="4">
            <v-card>
              <v-card-title class="text-h5 text-center">
                CRM Login
              </v-card-title>
              <v-card-text>
                <v-form @submit.prevent="handleLogin">
                  <v-text-field
                    v-model="username"
                    label="Username"
                    prepend-icon="mdi-account"
                    required></v-text-field>
                  <v-text-field
                    v-model="password"
                    label="Password"
                    type="password"
                    prepend-icon="mdi-lock"
                    required></v-text-field>
                  <v-alert v-if="error" type="error" class="mt-2">
                    {{ error }}
                  </v-alert>
                  <v-btn
                    type="submit"
                    color="primary"
                    block
                    class="mt-4"
                    :loading="loading">
                    Login
                  </v-btn>
                  <v-btn
                    text
                    block
                    class="mt-2"
                    @click="$router.push('/signup')">
                    Don't have an account? Sign up
                  </v-btn>
                </v-form>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </v-main>
  </v-app>
</template>

<script>
import axios from "axios";

export default {
  name: "Login",
  data() {
    return {
      username: "",
      password: "",
      error: "",
      loading: false,
    };
  },
  methods: {
    async handleLogin() {
      this.loading = true;
      this.error = "";
      try {
        const response = await axios.post("http://127.0.0.1:8000/api/token/", {
          username: this.username,
          password: this.password,
        });
        localStorage.setItem("access_token", response.data.access);
        localStorage.setItem("refresh_token", response.data.refresh);
        this.$router.push("/dashboard");
      } catch (err) {
        if (err.response?.status === 401) {
          this.error = "Invalid username or password. Please try again.";
        } else if (err.response?.data?.detail) {
          this.error = err.response.data.detail;
        } else if (err.message === 'Network Error') {
          this.error = "Unable to connect to the server. Please check your internet connection.";
        } else {
          this.error = "An error occurred during login. Please try again.";
        }
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
