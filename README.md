Supabase DB is frozen after 8 days of inactivity and has to be reactivated manually.

npm run dev in webUI folder to start webUI

paper_rows.csv contains a copy of the supabase database. It is to note that some entries were generated AFTER the dataset used in the thesis was created. Due to time constraints they could not be incorporated into the final paper.

The .env file has the openrouter API keys removed for security reasons, but the supabase API keys are necessary for it to work.

Supabase automatically invalidates the service key when it is added to the repository, so any program that needs to service key do not work and need a private sharing of the key.