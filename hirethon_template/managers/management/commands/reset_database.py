from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connection
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Clear all data from the database and create a superuser'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='admin@gmail.com',
            help='Email for the superuser (default: admin@gmail.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='qwertyuiop',
            help='Password for the superuser (default: qwertyuiop)'
        )
        parser.add_argument(
            '--name',
            type=str,
            default='Admin',
            help='Name for the superuser (default: Admin)'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        name = options['name']
        
        self.stdout.write(
            self.style.WARNING('⚠️  WARNING: This will delete ALL data from the database!')
        )
        self.stdout.write('Proceeding with database reset...')
        
        try:
            # Step 1: Clear all data from all tables
            self.clear_all_tables()
            
            # Step 2: Run migrations to ensure database schema is up to date
            self.stdout.write('Running migrations...')
            call_command('migrate', verbosity=0)
            
            # Step 3: Create superuser
            self.create_superuser(email, password, name)
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Database reset successful!')
            )
            self.stdout.write(
                self.style.SUCCESS(f'✅ Superuser created: {email}')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database reset failed: {str(e)}')
            )
            raise

    def clear_all_tables(self):
        """Clear all data from all tables"""
        self.stdout.write('🗑️  Clearing all database tables...')
        
        with connection.cursor() as cursor:
            try:
                # Get all table names (PostgreSQL)
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_type = 'BASE TABLE'
                """)
                tables = [row[0] for row in cursor.fetchall()]
                
                # Disable triggers temporarily (PostgreSQL equivalent of foreign key checks)
                cursor.execute("SET session_replication_role = replica")
                
                tables_cleared = 0
                # Clear each table
                for table in tables:
                    # Skip django_migrations table to avoid breaking migrations
                    if table == 'django_migrations':
                        continue
                    
                    try:
                        cursor.execute(f"DELETE FROM {table}")
                        # Reset sequence for auto-increment fields (PostgreSQL) - handle gracefully if no sequence exists
                        try:
                            cursor.execute(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), 1, false)")
                        except Exception:
                            # Table might not have an id sequence, that's fine
                            pass
                        tables_cleared += 1
                        self.stdout.write(f'  Cleared table: {table}')
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(f'  Could not clear table {table}: {str(e)}')
                        )
                
                # Re-enable triggers
                cursor.execute("SET session_replication_role = DEFAULT")
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Cleared {tables_cleared} tables')
                )
                
            except Exception as e:
                # Make sure to re-enable triggers even if something fails
                try:
                    cursor.execute("SET session_replication_role = DEFAULT")
                except:
                    pass
                raise

    def create_superuser(self, email, password, name):
        """Create a superuser with the provided credentials"""
        self.stdout.write('👤 Creating superuser...')
        
        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email {email} already exists. Updating...')
            )
            user = User.objects.get(email=email)
            user.set_password(password)
            user.name = name
            user.is_superuser = True
            user.is_staff = True
            user.is_manager = True
            user.is_active = True
            user.save()
            self.stdout.write('✅ Updated existing user to superuser')
        else:
            # Create new superuser
            user = User.objects.create_superuser(
                email=email,
                password=password,
                name=name,
            )
            self.stdout.write(f'✅ Created new superuser: {user.email}')
        
        # Verify the user was created correctly
        user.refresh_from_db()
        if user.is_superuser and user.is_staff and user.is_manager:
            self.stdout.write(
                self.style.SUCCESS(
                    f'🎉 Superuser verification successful:\n'
                    f'   Email: {user.email}\n'
                    f'   Name: {user.name}\n'
                    f'   Is Superuser: {user.is_superuser}\n'
                    f'   Is Staff: {user.is_staff}\n'
                    f'   Is Manager: {user.is_manager}'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR('❌ Superuser was not created with correct permissions')
            )
