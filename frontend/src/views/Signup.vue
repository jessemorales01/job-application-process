<template>
  <v-app>
    <v-main>
      <v-container fluid fill-height>
        <v-row align="center" justify="center">
          <v-col cols="12" sm="8" md="4">
            <v-card>
              <v-card-title class="text-h5 text-center">
                CRM Sign Up
              </v-card-title>
              <v-card-text>
                <v-form @submit.prevent="handleSignup">
                  <v-text-field
                    v-model="username"
                    label="Username"
                    prepend-icon="mdi-account"
                    required></v-text-field>
                  <v-text-field
                    v-model="email"
                    label="Email"
                    type="email"
                    prepend-icon="mdi-email"
                    required></v-text-field>
                  <v-text-field
                    v-model="password"
                    label="Password"
                    type="password"
                    prepend-icon="mdi-lock"
                    required></v-text-field>
                  <v-text-field
                    v-model="confirmPassword"
                    label="Confirm Password"
                    type="password"
                    prepend-icon="mdi-lock-check"
                    required></v-text-field>
                  <v-alert v-if="error" type="error" class="mt-2">
                    {{ error }}
                  </v-alert>
                  <v-alert v-if="success" type="success" class="mt-2">
                    {{ success }}
                  </v-alert>
                  <v-btn
                    type="submit"
                    color="primary"
                    block
                    class="mt-4"
                    :loading="loading">
                    Sign Up
                  </v-btn>
                  <v-btn
                    text
                    block
                    class="mt-2"
                    @click="$router.push('/login')">
                    Already have an account? Login
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
  name: "Signup",
  data() {
    return {
      username: "",
      email: "",
      password: "",
      confirmPassword: "",
      error: "",
      success: "",
      loading: false,
    };
  },
  methods: {
    async handleSignup() {
      this.loading = true;
      this.error = "";
      this.success = "";

      if (this.password !== this.confirmPassword) {
        this.error = "Passwords do not match";
        this.loading = false;
        return;
      }

      try {
        await axios.post("http://127.0.0.1:8000/api/register/", {
          username: this.username,
          email: this.email,
          password: this.password,
        });
        this.success = "Account created successfully! Redirecting to login...";
        setTimeout(() => {
          this.$router.push("/login");
        }, 2000);
      } catch (err) {
        this.error = err.response?.data?.username?.[0] || "Registration failed";
      } finally {
        this.loading = false;
      }
    },
  },
};
</script>
