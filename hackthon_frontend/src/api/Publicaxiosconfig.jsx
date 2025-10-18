import axios from 'axios';
const baseurl=import.meta.env.VITE_BASE_URL
const publicaxiosconfig = axios.create({
  baseURL: `${baseurl}/`,
  withCredentials: true,
  
});
export default publicaxiosconfig;

