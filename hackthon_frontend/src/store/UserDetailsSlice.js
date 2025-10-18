import { createSlice } from "@reduxjs/toolkit";
const UserDetailsSlice = createSlice({
  name: "userDetails",
  initialState: {
    id: "",
    name: "",
    email: "",
    is_manager: "",
    access_token: "",
    is_active: "",
  },
  reducers: {
    setUserDetails: (state, action) => {
      state.id = action.payload.id;
      state.name = action.payload.name;
      state.email = action.payload.email;
      state.is_manager = action.payload.is_manager;
      state.is_active = action.payload.is_active;
      state.access_token = action.payload.access_token;
    },

    destroyDetails: (state, action) => {
      state.id = '';
      state.name = '';
      state.email = '';
      state.is_manager = '';
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
