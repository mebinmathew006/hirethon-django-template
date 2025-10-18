import { createSlice } from "@reduxjs/toolkit";
const UserDetailsSlice = createSlice({
  name: "userDetails",
  initialState: {
    id: "",
    name: "",
    email: "",
    role: "",
    access_token: "",
    is_verified: "",
    is_active: "",
  },
  reducers: {
    setUserDetails: (state, action) => {
      state.id = action.payload.id;
      state.name = action.payload.name;
      state.email = action.payload.email;
      state.role = action.payload.role;
      state.is_verified = action.payload.is_verified;
      state.is_active = action.payload.is_active;
      state.access_token = action.payload.access_token;
    },

    destroyDetails: (state, action) => {
      state.id = '';
      state.name = '';
      state.email = '';
      state.role = '';
      state.is_verified = '';
      state.is_active = '';
      state.access_token = '';
    },

    updateAccessToken: (state, action) => {
      state.access_token = action.payload; // Only update access_token
    },
  },
});
export const { setUserDetails, destroyDetails, updateAccessToken } =
  UserDetailsSlice.actions;
export default UserDetailsSlice.reducer;
